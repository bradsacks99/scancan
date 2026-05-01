""" Pydantic Models """
from typing import Optional
from pydantic import BaseModel

class Version(BaseModel):
    """
    Version model representing the version information for ClamAV and ScanCan.

    Attributes:
        ClamAV (str): The version string for ClamAV.
        ScanCan (str): The version string for ScanCan.
    """
    ClamAV: str
    ScanCan: str

class Health(BaseModel):
    """
    Represents the health status of the application.

    Attributes:
        ping (str): A string indicating the ping status.
        version (Version): The version information of the application.
        stats (str): A string containing application statistics.
    """
    ping: str
    version: Version
    stats: str

class HealthResponse(BaseModel):
    """
    Represents the response for a health check.

    Attributes:
        response (Health): The health status of the application.
    """
    response: Health

class ScanResponse(BaseModel):
    """
    Represents the response for a file scan.

    Attributes:
        response (str): The result of the scan operation.
    """
    response: str

class ExceptionResponse(BaseModel):
    """
    Represents a generic exception response.

    Attributes:
        status_code (int): The HTTP status code for the exception.
        response (str): A message describing the exception.
    """
    status_code: int
    response: str

class VirusFoundResponse(ExceptionResponse):
    """
    Represents a response for a virus found during scanning.

    Attributes:
        path (Optional[str]): The path of the infected file, if available.
    """
    path: Optional[str] = None
