"""ScanCan Main entry point"""
import os
import re
from io import BytesIO
from typing import List
from fastapi import FastAPI, HTTPException, File, status
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from utils import get_clamav_connection
from config import *
from logger import Logger
from clamav import ClamAv
from aiofile import async_open

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

clamav = ClamAv()
clamav.set_logger(logger)
clamav.connecting()

@app.on_event("startup")
async def startup_event():
    """ Startup """
    logger.info("Starting up ScanCan")


@app.on_event("shutdown")
async def shutdown_event():
    """ Shutdown """
    logger.info("Shutting down ScanCan")

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    file_name = "favicon.ico"
    file_path = os.path.join(app.root_path, "static")
    return FileResponse(path=file_path, headers={"Content-Disposition": "attachment; filename=" + file_name})

@app.get("/ping")
async def ping():
    """
    GET /ping: attempts to ping ClamAv and returns the result
        Returns:
            result (object)
    """
    result = await clamav.ping()

    response = {"result": result}
    if not re.match(r'^PONG$', result):
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={'result': 'Unable to communicate with ClamAV'})
    return JSONResponse(status_code=status.HTTP_200_OK, content=response)

@app.post("/scanpath/{path:path}")
async def scan_path(path: str):
    """
    POST /scanpath: scan a mounted path with ClamAV
        Parameters:
            path (str): a path
        Returns:
            result (Object)
    """
    logger.info("Scanning path: %s" % path)
    result = await clamav.scan(path)

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
    result = await clamav.contscan(path)

    response = {"result": result}
    if re.match(r'^.*\sFOUND$', result):
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
    if len(file) > upload_size_limit:
        response = {'result': 'Max size %d bytes limit exceeded' % upload_size_limit}
        return JSONResponse(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, content=response)

    result = await clamav.instream(BytesIO(file))

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
