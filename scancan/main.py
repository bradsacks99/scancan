"""ScanCan Main entry point"""
import os
import re
from io import BytesIO
from typing import List
from fastapi import FastAPI, HTTPException, File, status
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from config import *
from logger import Logger
from aiofile import async_open
from aiopath import AsyncPath
from pyvalve import PyvalveNetwork

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

@app.on_event("startup")
async def startup_event():
    """ Startup """
    logger.info("Starting up ScanCan")


@app.on_event("shutdown")
async def shutdown_event():
    """ Shutdown """
    logger.info("Shutting down ScanCan")


@app.post("/scanfile")
async def scan_upload_file(file: bytes = File()):
    if len(file) > upload_size_limit:
        response = {'result': 'Max size %d bytes limit exceeded' % upload_size_limit}
        return JSONResponse(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, content=response)
    pvs = await PyvalveNetwork(clamd_host, clamd_port)
    result = await pvs.instream(BytesIO(file))
    response = {"result": result}
    if re.match(r'^.*\sFOUND$', result):
        return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE, content=response)
    return JSONResponse(status_code=status.HTTP_200_OK, content=response)

@app.get("/license", response_class=PlainTextResponse)
async def show_license():
    """
    License: view the ScanCan license
    """
    license_file = 'LICENSE'
    chk_path = AsyncPath(license_file)
    if not await chk_path.exists():
        logger.info("Looks like we're running local. Try the root directory of ScanCan")
        license_file = '../LICENSE'
    chk_path = AsyncPath(license_file)
    if not await chk_path.exists():
        raise HTTPException(status_code=404, detail="License not found")
    async with async_open(license_file, 'r') as fh:
        output = await fh.read()
    return output
