"""ScanCan Main entry point"""
import asyncio
from contextlib import asynccontextmanager
import os
import re
from typing import Annotated
import urllib
from io import BytesIO

import aiohttp
from aiofile import async_open
from fastapi import Depends, FastAPI, File, Request, status
from fastapi.responses import PlainTextResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pyvalve import PyvalveResponseError, PyvalveConnectionError, PyvalveScanningError

import config as conf
from clamav import ClamAv
from logger import Logger
from models import ExceptionResponse, Health, HealthResponse, ScanResponse, VirusFoundResponse

logger = Logger(name='ScanCan').get_logger()

app = FastAPI(
    title="ScanCan",
    description="Virus Scanning API for ClamAV",
    version="0.1.0",
    static_directory='static',
    swagger_static={
        "favicon": 'favicon.ico',
    },
)

app.mount("/static", StaticFiles(directory="static"), name="static")

class VirusFoundException(Exception):
    """ Virus Found Exception """
    def __init__(self, status_code: int, response: str, path: str = None):
        self.status_code = status_code
        self.response = response
        self.path = path

class ScanException(Exception):
    """ Scan Exception """
    def __init__(self, status_code: int, response: str):
        self.status_code = status_code
        self.response = response

@app.exception_handler(VirusFoundException)
async def virus_found_exception_handler(request: Request, exc: VirusFoundException):
    """ Scan Exception Handler """
    error_model = VirusFoundResponse(
        status_code=exc.status_code,
        response=exc.response
    )

    if exc.path:
        error_model.path=exc.path

    return JSONResponse(
        status_code=exc.status_code,
        content=error_model.model_dump(exclude_unset=True)
    )

@app.exception_handler(ScanException)
async def scan_exception_handler(request: Request, exc: ScanException):
    """ Scan Exception Handler """
    return JSONResponse(
        status_code=exc.status_code,     
        content=ExceptionResponse(
            status_code=exc.status_code,
            response=exc.response
        ).model_dump()
    )

class ClamInstance:
    """ ClamInstance Singleton Dependency """
    _instance = None

    async def __new__(cls):
        if cls._instance is None:
            logger.info("Setting up ClamAV connection")
            cls._instance = ClamAv(conf)
            cls._instance.set_logger(logger)
            await cls._instance.connecting()
        return cls._instance

async def clamav_init() -> ClamAv:
    """ ClamAv Dependency """
    clamav = await ClamInstance()
    return clamav

@asynccontextmanager
async def lifespan(app: FastAPI):
    """ Lifespan """
    logger.info("Starting up ScanCan")
    yield
    logger.info("Shutting down ScanCan")

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    """ Favicon """
    file_path = os.path.join(app.root_path, "static", "favicon.ico")
    return FileResponse(path=file_path)


@app.get("/health",
         status_code=status.HTTP_200_OK,
         responses={
            status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ExceptionResponse},
            status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ExceptionResponse}
        }
    )
async def health(clamav: Annotated[ClamAv, Depends(clamav_init)]) -> HealthResponse:
    """
    GET /health: determine the health of ScanCan
        Returns:
            result (object)
    """
    try:
        ping_result = await clamav.ping()
    except PyvalveConnectionError as err:
        raise ScanException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            response='ClamAV connection error.'
        ) from err

    if not re.match(r'^PONG$', ping_result):
        logger.error(ping_result)
        raise ScanException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            response='Unable to communicate with ClamAV'
        )

    stats_result = await clamav.stats()

    regex = re.compile(r'^POOLS:.*\n\nSTATE:\sVALID\sPRIMARY\n', re.MULTILINE)
    if not re.match(regex, stats_result):
        logger.error(stats_result)
        raise ScanException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            response='Invalid response from ClamAV'
        )

    return HealthResponse(response=Health(ping=ping_result, stats=stats_result)).model_dump()


@app.post("/scanpath/{path:path}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"model": ScanResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ExceptionResponse},
        status.HTTP_406_NOT_ACCEPTABLE: {"model": VirusFoundResponse}
        }
    )
async def scan_path(path: str, clamav: Annotated[ClamAv, Depends(clamav_init)]):
    """
    POST /scanpath: scan a mounted path with ClamAV
        Parameters:
            path (str): a path
        Returns:
            result (ScanResponse)
    """
    logger.info("Scanning path: %s" % path)
    try:
        result = await clamav.scan(path)
    except PyvalveResponseError as err:
        logger.exception(str(err))
        raise ScanException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            response='Error scannning'
        ) from err
    except PyvalveScanningError as err:
        logger.exception(str(err))
        raise ScanException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            response='Error scannning'
        ) from err

    if re.match(r'^.*\sFOUND$', result):
        raise VirusFoundException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            response=result,
            path=path
        )

    return ScanResponse(response=result).model_dump()


@app.get("/scanurl/",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"model": ScanResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ExceptionResponse},
        status.HTTP_404_NOT_FOUND: {"model": ExceptionResponse},
        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: {"model": ExceptionResponse},
        status.HTTP_406_NOT_ACCEPTABLE: {"model": VirusFoundResponse}
        }
    )
async def scan_url(url: str, clamav: Annotated[ClamAv, Depends(clamav_init)]):
    """
    GET /scanurl: scan a url with ClamAV
        Parameters:
            url (str): a url
        Returns:
            result (Object)
    """

    sema = asyncio.BoundedSemaphore(5)
    data = ''
    url = urllib.parse.unquote(url).strip()
    logger.info(f"The url is: {url}")
    try:
        async with sema, aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                else:
                    raise ScanException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        response=f"{url} not found")
    except aiohttp.client_exceptions.InvalidURL as err:
        logger.error(err)
        raise ScanException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            response="Invalid URL") from err
    if len(data) > conf.upload_size_limit:
        raise ScanException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,                
            response=f'Max size {conf.upload_size_limit} bytes limit exceeded')

    try:
        result = await clamav.instream(BytesIO(data))
    except PyvalveScanningError as err:
        logger.exception()
        raise ScanException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            response="Error scanning stream") from err

    if re.match(r'^.*\sFOUND$', result):
        raise VirusFoundException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            response=result,
            path=url
        )
    return ScanResponse(response=result).model_dump()


@app.post("/contscan/{path:path}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"model": ScanResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ExceptionResponse},
        status.HTTP_406_NOT_ACCEPTABLE: {"model": VirusFoundResponse}
    }
)
async def cont_scan(path: str, clamav: Annotated[ClamAv, Depends(clamav_init)]):
    """
    POST /contscan: scan a mounted path with ClamAV, continue if found
        Parameters:
            path (str): a path
        Returns:
            result (Object)
    """
    logger.info("Scanning path: %s" % path)
    try:
        result = await clamav.contscan(path)
    except PyvalveScanningError as err:
        logger.exception(err)
        raise ScanException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            response="Error scanning (cont)") from err

    regex = re.compile(r'^.*\sFOUND', re.MULTILINE)
    if re.match(regex, result):
        raise VirusFoundException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            response=result,
            path=path)
    return ScanResponse(status_code=status.HTTP_200_OK, response=result).model_dump()


@app.post("/scanfile",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"model": ScanResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ExceptionResponse},
        status.HTTP_406_NOT_ACCEPTABLE: {"model": VirusFoundResponse},
        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: {"model": ExceptionResponse}
    }
)
async def scan_upload_file(clamav: Annotated[ClamAv, Depends(clamav_init)], file: bytes = File()):
    """
    POST /scanfile: scan a file stream with ClamAV
        Parameters:
            file (bytes): an uploaded file
        Returns:
            result (Object)
    """
    if len(file) > conf.upload_size_limit:
        raise ScanException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            response=f'Max size {conf.upload_size_limit} bytes limit exceeded')

    try:
        result = await clamav.instream(BytesIO(file))
    except PyvalveScanningError as err:
        logger.exception()
        raise ScanException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            response="Error scanning file") from err

    if re.match(r'^.*\sFOUND$', result):
        raise VirusFoundException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            response=result)

    return ScanResponse(
        status_code=status.HTTP_200_OK,
        response=result).model_dump()


@app.get("/license", response_class=PlainTextResponse)
async def show_license():
    """
    GET /license: view the ScanCan license
        Returns:
            license (string)
    """
    license_file = 'LICENSE'

    async with async_open(license_file, 'r') as fh:
        output = await fh.read()
    return output
