"""ScanCan Main entry point"""
import asyncio
import os
import re
import urllib
from io import BytesIO

import aiohttp
from aiofile import async_open
from fastapi import FastAPI, File, Request, status
from fastapi.responses import PlainTextResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pyvalve import PyvalveResponseError, PyvalveConnectionError, PyvalveScanningError

import config as conf
from clamav import ClamAv
from logger import Logger
from scancan.models import ExceptionResponse, ScanResponse, VirusFoundResponse

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

clamav = None

app.mount("/static", StaticFiles(directory="static"), name="static")

class ScanException(Exception):
    """ Scan Exception """
    def __init__(self, status_code: int, response: str):
        self.status_code = status_code
        self.response = response

@app.exception_handler(ScanException)
async def custom_exception_handler(request: Request, exc: ScanException):
    """ Scan Exception Handler """
    return JSONResponse(
        status_code=exc.status_code,     
        content=ExceptionResponse(
            status_code=exc.status_code,
            response=exc.response
        ).model_dump()
    )

@app.on_event("startup")
async def startup_event():
    """ Startup """
    logger.info("Starting up ScanCan")
    global clamav
    clamav = ClamAv(conf)
    clamav.set_logger(logger)
    await clamav.connecting()


@app.on_event("shutdown")
async def shutdown_event():
    """ Shutdown """
    logger.info("Shutting down ScanCan")


@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    file_path = os.path.join(app.root_path, "static", "favicon.ico")
    return FileResponse(path=file_path)


@app.get("/health")
async def health():
    """
    GET /health: determine the health of ScanCan
        Returns:
            result (object)
    """
    try:
        ping_result = await clamav.ping()
    except PyvalveConnectionError as err:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content={'result': 'ClamAV connection error.'})

    if not re.match(r'^PONG$', ping_result):
        logger.error(ping_result)
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            content={'result': 'Unable to communicate with ClamAV'})

    stats_result = await clamav.stats()

    regex = re.compile(r'^POOLS:.*\n\nSTATE:\sVALID\sPRIMARY\n', re.MULTILINE)
    if not re.match(regex, stats_result):
        logger.error(stats_result)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content={'result': 'Invalid response from ClamAV'})

    response = {"result": {"ping": ping_result, "stats": stats_result}}
    return JSONResponse(status_code=status.HTTP_200_OK, content=response)


@app.post("/scanpath/{path:path}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ExceptionResponse},
        status.HTTP_406_NOT_ACCEPTABLE: {"model": VirusFoundResponse}}
    )
async def scan_path(path: str) -> ScanResponse:
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
        return VirusFoundResponse(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            response=result,
            path=path
        ).model_dump()

    return ScanResponse(response=result).model_dump()


@app.get("/scanurl/")
async def scan_url(url: str):
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
                    response = {"result": f"{url} not found"}
                    return JSONResponse(
                        status_code=status.HTTP_404_NOT_FOUND,
                        content=response)
    except aiohttp.client_exceptions.InvalidURL as exp:
        logger.error(exp)
        response = {"result": "Invalid URL"}
        return JSONResponse(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            content=response)
    if len(data) > conf.upload_size_limit:
        response = {'result': 'Max size %d bytes limit exceeded' % conf.upload_size_limit}
        return JSONResponse(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, content=response)

    try:
        result = await clamav.instream(BytesIO(data))
    except PyvalveScanningError as err:
        logger.exception()
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content="Error scanning stream")

    response = {"result": result}
    if re.match(r'^.*\sFOUND$', result):
        return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE, content=response)
    return JSONResponse(status_code=status.HTTP_200_OK, content=response)


@app.post("/contscan/{path:path}")
async def cont_scan(path: str):
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
        logger.exception()
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content="Error scanning (cont)")

    response = {"result": result}
    regex = re.compile(r'^.*\sFOUND', re.MULTILINE)
    if re.match(regex, result):
        return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE, content=response)
    return JSONResponse(status_code=status.HTTP_200_OK, content=response)


@app.post("/scanfile")
async def scan_upload_file(file: bytes = File()):
    """
    POST /scanfile: scan a file stream with ClamAV
        Parameters:
            file (bytes): an uploaded file
        Returns:
            result (Object)
    """
    if len(file) > conf.upload_size_limit:
        response = {'result': 'Max size %d bytes limit exceeded' % conf.upload_size_limit}
        return JSONResponse(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, content=response)

    try:
        result = await clamav.instream(BytesIO(file))
    except PyvalveScanningError as err:
        logger.exception()
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content="Error scanning file")

    response = {"result": result}
    if re.match(r'^.*\sFOUND$', result):
        return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE, content=response)
    return JSONResponse(status_code=status.HTTP_200_OK, content=response)


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
