import aiohttp
import pytest

import src.main as main_module
from fastapi.testclient import TestClient
from fastapi import HTTPException
from src.main import app, clamav_init

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clear_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def _make_fake_clamav(**methods):
    wrapped = {k: staticmethod(v) for k, v in methods.items()}
    return type("FakeClamAV", (), wrapped)()


def _override_clamav(fake):
    app.dependency_overrides[clamav_init] = lambda: fake


def _fake_client_session(status=200, data=b"file content"):
    class FakeResp:
        def __init__(self):
            self.status = status

        async def read(self):
            return data

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

    class FakeSession:
        def get(self, url):
            return FakeResp()

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

    return FakeSession


def test_authenticate_defaults_to_allow_when_addon_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    # No addon module present means auth is bypassed.
    main_module.authenticate("any-token")


def test_authenticate_uses_addon_module(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    addon_dir = tmp_path / "addon"
    addon_dir.mkdir(parents=True)
    addon_file = addon_dir / "authentication.py"
    addon_file.write_text(
        "def authenticate(token):\n"
        "    return token == 'good-token'\n",
        encoding="utf-8",
    )

    main_module.authenticate("good-token")


def test_authenticate_raises_unauthorized_when_addon_returns_false(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    addon_dir = tmp_path / "addon"
    addon_dir.mkdir(parents=True)
    addon_file = addon_dir / "authentication.py"
    addon_file.write_text(
        "def authenticate(token):\n"
        "    return False\n",
        encoding="utf-8",
    )

    with pytest.raises(HTTPException) as exc:
        main_module.authenticate("bad-token")

    assert exc.value.status_code == 401


def test_authenticate_raises_when_addon_missing_authenticate_function(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    addon_dir = tmp_path / "addon"
    addon_dir.mkdir(parents=True)
    addon_file = addon_dir / "authentication.py"
    addon_file.write_text("x = 1\n", encoding="utf-8")

    with pytest.raises(RuntimeError) as exc:
        main_module.authenticate("token")

    assert "authenticate(token)" in str(exc.value)


def test_health():
    async def fake_ping():
        return "PONG"

    async def fake_stats():
        return "POOLS:\n\nSTATE: VALID PRIMARY\n"

    async def fake_version():
        return "ClamAV 0.103.2"

    fake = _make_fake_clamav(ping=fake_ping, stats=fake_stats, version=fake_version)
    _override_clamav(fake)

    response = client.get("/health")

    assert response.status_code == 200
    assert "ping" in response.json()["response"]


def test_health_connection_error(monkeypatch):
    class FakeConnectionError(Exception):
        pass

    monkeypatch.setattr(main_module, "PyvalveConnectionError", FakeConnectionError)

    async def fake_ping():
        raise FakeConnectionError("down")

    async def fake_stats():
        return "unused"

    async def fake_version():
        return "unused"

    fake = _make_fake_clamav(ping=fake_ping, stats=fake_stats, version=fake_version)
    _override_clamav(fake)

    response = client.get("/health")

    assert response.status_code == 500
    assert response.json()["response"] == "ClamAV connection error."


def test_health_unhealthy_ping():
    async def fake_ping():
        return "NOPE"

    async def fake_stats():
        return "POOLS:\n\nSTATE: VALID PRIMARY\n"

    async def fake_version():
        return "ClamAV 0.103.2"

    fake = _make_fake_clamav(ping=fake_ping, stats=fake_stats, version=fake_version)
    _override_clamav(fake)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["response"] == "Unable to communicate with ClamAV"


def test_health_invalid_stats():
    async def fake_ping():
        return "PONG"

    async def fake_stats():
        return "STATE: BROKEN"

    async def fake_version():
        return "ClamAV 0.103.2"

    fake = _make_fake_clamav(ping=fake_ping, stats=fake_stats, version=fake_version)
    _override_clamav(fake)

    response = client.get("/health")

    assert response.status_code == 500
    assert response.json()["response"] == "Invalid response from ClamAV"


def test_scan_path():
    async def fake_scan(path):
        return "OK"

    fake = _make_fake_clamav(scan=fake_scan)
    _override_clamav(fake)

    response = client.post("/scanpath/somefile.txt")

    assert response.status_code == 200
    assert response.json()["response"] == "OK"


def test_scan_path_virus_found():
    async def fake_scan(path):
        return "Eicar FOUND"

    fake = _make_fake_clamav(scan=fake_scan)
    _override_clamav(fake)

    response = client.post("/scanpath/somefile.txt")

    assert response.status_code == 406
    assert response.json()["path"] == "somefile.txt"


def test_scan_path_response_error(monkeypatch):
    class FakeResponseError(Exception):
        pass

    monkeypatch.setattr(main_module, "PyvalveResponseError", FakeResponseError)

    async def fake_scan(path):
        raise FakeResponseError("bad")

    fake = _make_fake_clamav(scan=fake_scan)
    _override_clamav(fake)

    response = client.post("/scanpath/somefile.txt")

    assert response.status_code == 500
    assert response.json()["response"] == "Error scanning"


def test_scan_path_scanning_error(monkeypatch):
    class FakeScanningError(Exception):
        pass

    monkeypatch.setattr(main_module, "PyvalveScanningError", FakeScanningError)

    async def fake_scan(path):
        raise FakeScanningError("bad")

    fake = _make_fake_clamav(scan=fake_scan)
    _override_clamav(fake)

    response = client.post("/scanpath/somefile.txt")

    assert response.status_code == 500
    assert response.json()["response"] == "Error scanning"


def test_scan_url(monkeypatch):
    async def fake_instream(data):
        return "OK"

    fake = _make_fake_clamav(instream=fake_instream)
    _override_clamav(fake)
    monkeypatch.setattr(aiohttp, "ClientSession", _fake_client_session())

    response = client.get("/scanurl/?url=https://example.com")

    assert response.status_code == 200
    assert response.json()["response"] == "OK"


def test_scan_url_not_found(monkeypatch):
    async def fake_instream(data):
        return "OK"

    fake = _make_fake_clamav(instream=fake_instream)
    _override_clamav(fake)
    monkeypatch.setattr(aiohttp, "ClientSession", _fake_client_session(status=404))

    response = client.get("/scanurl/?url=https://example.com/missing")

    assert response.status_code == 404
    assert "not found" in response.json()["response"]


def test_scan_url_invalid_url(monkeypatch):
    async def fake_instream(data):
        return "OK"

    class BadSession:
        def get(self, url):
            raise aiohttp.client_exceptions.InvalidURL(url)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

    fake = _make_fake_clamav(instream=fake_instream)
    _override_clamav(fake)
    monkeypatch.setattr(aiohttp, "ClientSession", lambda: BadSession())

    response = client.get("/scanurl/?url=://not-a-url")

    assert response.status_code == 406
    assert response.json()["response"] == "Invalid URL"


def test_scan_url_too_large(monkeypatch):
    async def fake_instream(data):
        return "OK"

    fake = _make_fake_clamav(instream=fake_instream)
    _override_clamav(fake)
    monkeypatch.setattr(aiohttp, "ClientSession", _fake_client_session(data=b"12345"))
    monkeypatch.setattr(main_module.conf, "UPLOAD_SIZE_LIMIT", 4)

    response = client.get("/scanurl/?url=https://example.com")

    assert response.status_code == 413
    assert "limit exceeded" in response.json()["response"]


def test_scan_url_scanning_error(monkeypatch):
    class FakeScanningError(Exception):
        pass

    monkeypatch.setattr(main_module, "PyvalveScanningError", FakeScanningError)

    async def fake_instream(data):
        raise FakeScanningError("scan failed")

    fake = _make_fake_clamav(instream=fake_instream)
    _override_clamav(fake)
    monkeypatch.setattr(aiohttp, "ClientSession", _fake_client_session())

    response = client.get("/scanurl/?url=https://example.com")

    assert response.status_code == 500
    assert response.json()["response"] == "Error scanning stream"


def test_scan_url_virus_found(monkeypatch):
    async def fake_instream(data):
        return "Eicar FOUND"

    fake = _make_fake_clamav(instream=fake_instream)
    _override_clamav(fake)
    monkeypatch.setattr(aiohttp, "ClientSession", _fake_client_session())

    response = client.get("/scanurl/?url=https://example.com/file.bin")

    assert response.status_code == 406
    assert response.json()["path"] == "https://example.com/file.bin"


def test_cont_scan():
    async def fake_contscan(path):
        return "OK"

    fake = _make_fake_clamav(contscan=fake_contscan)
    _override_clamav(fake)

    response = client.post("/contscan/somefile.txt")

    assert response.status_code == 200
    assert response.json()["response"] == "OK"


def test_cont_scan_scanning_error(monkeypatch):
    class FakeScanningError(Exception):
        pass

    monkeypatch.setattr(main_module, "PyvalveScanningError", FakeScanningError)

    async def fake_contscan(path):
        raise FakeScanningError("bad")

    fake = _make_fake_clamav(contscan=fake_contscan)
    _override_clamav(fake)

    response = client.post("/contscan/somefile.txt")

    assert response.status_code == 500
    assert response.json()["response"] == "Error scanning (cont)"


def test_cont_scan_virus_found():
    async def fake_contscan(path):
        return "foo FOUND\nbar"

    fake = _make_fake_clamav(contscan=fake_contscan)
    _override_clamav(fake)

    response = client.post("/contscan/somefile.txt")

    assert response.status_code == 406
    assert response.json()["path"] == "somefile.txt"


def test_scan_upload_file():
    async def fake_instream(data):
        return "OK"

    fake = _make_fake_clamav(instream=fake_instream)
    _override_clamav(fake)

    response = client.post("/scanfile", files={"file": b"test"})

    assert response.status_code == 200
    assert response.json()["response"] == "OK"


def test_scan_upload_file_too_large(monkeypatch):
    async def fake_instream(data):
        return "OK"

    fake = _make_fake_clamav(instream=fake_instream)
    _override_clamav(fake)
    monkeypatch.setattr(main_module.conf, "UPLOAD_SIZE_LIMIT", 3)

    response = client.post("/scanfile", files={"file": b"test"})

    assert response.status_code == 413
    assert "limit exceeded" in response.json()["response"]


def test_scan_upload_file_scanning_error(monkeypatch):
    class FakeScanningError(Exception):
        pass

    monkeypatch.setattr(main_module, "PyvalveScanningError", FakeScanningError)

    async def fake_instream(data):
        raise FakeScanningError("bad")

    fake = _make_fake_clamav(instream=fake_instream)
    _override_clamav(fake)

    response = client.post("/scanfile", files={"file": b"test"})

    assert response.status_code == 500
    assert response.json()["response"] == "Error scanning file"


def test_scan_upload_file_virus_found():
    async def fake_instream(data):
        return "Eicar FOUND"

    fake = _make_fake_clamav(instream=fake_instream)
    _override_clamav(fake)

    response = client.post("/scanfile", files={"file": b"test"})

    assert response.status_code == 406
    assert response.json()["response"] == "Eicar FOUND"


def test_show_license(monkeypatch):
    class AsyncFileMock:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def read(self):
            return "MIT License"

    monkeypatch.setattr("src.main.async_open", lambda *a, **k: AsyncFileMock())

    response = client.get("/license")

    assert response.status_code == 200
    assert "MIT License" in response.text
