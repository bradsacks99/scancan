"""Tests for src/models.py."""

import pytest
from pydantic import ValidationError

from src.models import (
    ExceptionResponse,
    Health,
    HealthResponse,
    ScanResponse,
    Version,
    VirusFoundResponse,
)


def test_version_model_creation():
    model = Version(ClamAV="1.4.2", ScanCan="0.1.0")

    assert model.ClamAV == "1.4.2"
    assert model.ScanCan == "0.1.0"


def test_health_model_with_nested_version():
    version = Version(ClamAV="1.4.2", ScanCan="0.1.0")
    health = Health(ping="PONG", version=version, stats="STATE: VALID PRIMARY")

    assert health.ping == "PONG"
    assert health.version.ClamAV == "1.4.2"
    assert health.stats == "STATE: VALID PRIMARY"


def test_health_response_from_nested_dict():
    payload = {
        "response": {
            "ping": "PONG",
            "version": {"ClamAV": "1.4.2", "ScanCan": "0.1.0"},
            "stats": "STATE: VALID PRIMARY",
        }
    }

    model = HealthResponse(**payload)

    assert model.response.ping == "PONG"
    assert model.response.version.ScanCan == "0.1.0"


def test_scan_response_model_creation():
    model = ScanResponse(response="OK")

    assert model.response == "OK"


def test_exception_response_model_creation():
    model = ExceptionResponse(status_code=500, response="Error scanning")

    assert model.status_code == 500
    assert model.response == "Error scanning"


def test_virus_found_response_default_path_none():
    model = VirusFoundResponse(status_code=406, response="Eicar FOUND")

    assert model.path is None
    assert model.status_code == 406


def test_virus_found_response_with_path():
    model = VirusFoundResponse(
        status_code=406,
        response="Eicar FOUND",
        path="/tmp/eicar.txt",
    )

    assert model.path == "/tmp/eicar.txt"
    assert model.model_dump()["path"] == "/tmp/eicar.txt"


def test_validation_error_when_required_fields_missing():
    with pytest.raises(ValidationError):
        Version(ClamAV="1.4.2")

    with pytest.raises(ValidationError):
        ExceptionResponse(response="Error scanning")
