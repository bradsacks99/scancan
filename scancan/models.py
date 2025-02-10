""" Pydantic Models """
from pydantic import BaseModel

class ScanResponse(BaseModel):
    response: str

class ExceptionResponse(BaseModel):
    status_code: int
    response: str

class VirusFoundResponse(ExceptionResponse):
    path: str