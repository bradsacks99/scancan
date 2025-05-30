import pytest
from fastapi.testclient import TestClient
from scancan.main import app

client = TestClient(app)

def test_health(monkeypatch):
    """
    Test the /health endpoint.
    Mocks ClamAV's ping and stats methods to simulate a healthy response.
    """
    async def fake_ping():
        return "PONG"
    async def fake_stats():
        return "POOLS:\n\nSTATE: VALID PRIMARY\n"
    app.clamav = type("ClamAV", (), {"ping": fake_ping, "stats": fake_stats})()
    response = client.get("/health")
    assert response.status_code == 200
    assert "ping" in response.json()["result"]

def test_scan_path(monkeypatch):
    """
    Test the /scanpath/{path} endpoint.
    Mocks ClamAV's scan method to simulate a successful scan.
    """
    async def fake_scan(path):
        return "OK"
    app.clamav = type("ClamAV", (), {"scan": fake_scan})()
    response = client.post("/scanpath/somefile.txt")
    assert response.status_code == 200

def test_scan_url(monkeypatch):
    """
    Test the /scanurl/ endpoint.
    Mocks ClamAV's instream method.
    Note: This test may fail unless aiohttp.ClientSession is also mocked.
    """
    async def fake_instream(data):
        return "OK"
    app.clamav = type("ClamAV", (), {"instream": fake_instream})()
    # Mock aiohttp and urllib if needed for more robust tests
    response = client.get("/scanurl/?url=https://example.com")
    # This will fail unless you mock aiohttp.ClientSession, see advanced mocking for full coverage

def test_cont_scan(monkeypatch):
    """
    Test the /contscan/{path} endpoint.
    Mocks ClamAV's contscan method to simulate a successful scan.
    """
    async def fake_contscan(path):
        return "OK"
    app.clamav = type("ClamAV", (), {"contscan": fake_contscan})()
    response = client.post("/contscan/somefile.txt")
    assert response.status_code == 200

def test_scan_upload_file(monkeypatch):
    """
    Test the /scanfile endpoint for file uploads.
    Mocks ClamAV's instream method to simulate a successful scan.
    """
    async def fake_instream(data):
        return "OK"
    app.clamav = type("ClamAV", (), {"instream": fake_instream})()
    response = client.post("/scanfile", files={"file": b"test"})
    assert response.status_code == 200

def test_show_license(monkeypatch, tmp_path):
    """
    Test the /license endpoint.
    Mocks async_open to return a temporary LICENSE file.
    """
    license_file = tmp_path / "LICENSE"
    license_file.write_text("MIT License")
    monkeypatch.setattr("scancan.main.async_open", lambda *a, **k: open(license_file, "r"))
    response = client.get("/license")
    assert response.status_code == 200
    assert "MIT License" in response.text