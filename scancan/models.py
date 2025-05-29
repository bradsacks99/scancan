""" Pydantic Models """
from typing import Optional
from pydantic import BaseModel

class Health(BaseModel):
    ping: str
    stats: str

class HealthResponse(BaseModel):
    response: Health

class ScanResponse(BaseModel):
    response: str

class ExceptionResponse(BaseModel):
    status_code: int
    response: str

class VirusFoundResponse(ExceptionResponse):
    path: Optional[str] = None