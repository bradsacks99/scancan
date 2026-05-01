"""ScanCan Main entry point"""
import asyncio
import importlib.util
import os
import re
import urllib
from io import BytesIO
from pathlib import Path

from typing_extensions import Annotated

import aiohttp
from aiofile import async_open
from pyvalve import PyvalveResponseError, PyvalveConnectionError, PyvalveScanningError

from fastapi import Depends, FastAPI, File, HTTPException, Request, status
from fastapi.responses import PlainTextResponse, JSONResponse, FileResponse

import config as conf
from clamav import ClamAv
from logger import Logger
from models import (
    ExceptionResponse,
    Health,
    HealthResponse,
    ScanResponse,
    Version,
    VirusFoundResponse,
)

logger: Logger = Logger(name='ScanCan').get_logger()

app = FastAPI(
    title="ScanCan",
    description="Virus Scanning API for ClamAV",
    version=conf.SCAN_CAN_VERSION,
)


def _load_authentication_module():
    """Load optional addon authentication module from addon/authentication.py."""
    auth_addon_file = Path("addon/authentication.py")

    if not auth_addon_file.is_file():
        logger.info("No addon authentication module found at %s", auth_addon_file)
        return None

    spec = importlib.util.spec_from_file_location("scancan_addon_authentication", auth_addon_file)
    if not spec or not spec.loader:
        logger.warning("Unable to load addon authentication module spec from %s", auth_addon_file)
        return None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "authenticate") or not callable(module.authenticate):
        raise RuntimeError("Addon authentication module must define authenticate(token)")
    return module

# Authentication dependency
def authenticate(token: str):
    """
    Authenticates the user by verifying the provided token.

    Args:
        token (str): The token to verify.

    Raises:
        HTTPException: If the token is invalid or missing.
    """
    module = _load_authentication_module()
    if module is None:
        return

    result = module.authenticate(token)
    if result is False:
        raise HTTPException(status_code=401, detail="Unauthorized")

# Apply authentication conditionally
if conf.USE_AUTHENTICATION:
    @app.middleware("http")
    async def authentication_middleware(request, call_next):
        """ User Authentication Middleware """
        if request.url.path not in ["/health", "/license", "/docs", "/static"]:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Unauthorized")
            token = auth_header.removeprefix("Bearer ").strip()
            authenticate(token)
        response = await call_next(request)
        return response

class VirusFoundException(Exception):
    """ Virus Found Exception """
    def __init__(self, status_code: int, response: str, path: str = ''):
        self.status_code = status_code
        self.response = response
        self.path = path

class ScanException(Exception):
    """ Scan Exception """
    def __init__(self, status_code: int, response: str):
        self.status_code = status_code
        self.response = response

@app.exception_handler(VirusFoundException)
async def virus_found_exception_handler(request: Request, exc: VirusFoundException): # pylint: disable=unused-argument
    """ Scan Exception Handler """
    error_model = VirusFoundResponse(
        status_code=exc.status_code,
        response=exc.response
    )

    if exc.path:
        error_model.path = exc.path

    return JSONResponse(
        status_code=exc.status_code,
        content=error_model.model_dump(exclude_unset=True)
    )

@app.exception_handler(ScanException)
async def scan_exception_handler(request: Request, exc: ScanException): # pylint: disable=unused-argument
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

    def __new__(cls):
        if cls._instance is None:
            logger.info("Setting up ClamAV connection")
            cls._instance = ClamAv(conf)
            cls._instance.set_logger(logger)
        return cls._instance

    async def initialize(self):
        """
        Asynchronously initializes the instance by establishing a connection.

        This method checks if the `_instance` attribute is set and, if so, 
        calls its `connecting` method to perform the connection process.

        Returns:
            None
        """
        if self._instance:
            await self._instance.connecting()

async def clamav_init() -> ClamAv:
    """ ClamAv Dependency """
    clamav = ClamInstance()
    return clamav

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    """
    Handles requests for the favicon.ico file.

    Returns:
        FileResponse: The favicon.ico file located in the static directory.

    Notes:
        - This endpoint is excluded from the OpenAPI schema.
        - The favicon is served from the 'static' folder within the application's root path.
    """
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
        version_result = await clamav.version()
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

    return HealthResponse(response=Health(
        ping=ping_result,
        version=Version(ClamAV=version_result, ScanCan=conf.SCAN_CAN_VERSION),
        stats=stats_result)).model_dump()

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
    logger.info("Scanning path: %s", path)
    try:
        result = await clamav.scan(path)
    except PyvalveResponseError as err:
        logger.exception(str(err))
        raise ScanException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            response='Error scanning'
        ) from err
    except PyvalveScanningError as err:
        logger.exception(str(err))
        raise ScanException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            response='Error scanning'
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
    data = b''
    url = urllib.parse.unquote(url).strip()
    logger.info("The url is: %s", url)
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
    if len(data) > conf.UPLOAD_SIZE_LIMIT:
        raise ScanException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            response=f'Max size {conf.UPLOAD_SIZE_LIMIT} bytes limit exceeded')

    try:
        result = await clamav.instream(BytesIO(data))
    except PyvalveScanningError as err:
        logger.exception(str(err))
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
    logger.info("Scanning path: %s", path)
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
    return ScanResponse(response=result).model_dump()

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
    if len(file) > conf.UPLOAD_SIZE_LIMIT:
        raise ScanException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            response=f'Max size {conf.UPLOAD_SIZE_LIMIT} bytes limit exceeded')

    try:
        result = await clamav.instream(BytesIO(file))
    except PyvalveScanningError as err:
        logger.exception(str(err))
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
