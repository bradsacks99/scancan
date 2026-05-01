"""Tests for src/clamav.py"""
from types import SimpleNamespace

import pytest

from src.clamav import ClamAv, PyvalveConnectionError


class DummyLogger:
    """Simple logger stub for tests."""

    def __init__(self):
        self.messages = []

    def info(self, msg):
        self.messages.append(msg)


class FakePVS:
    """Async fake pyvalve client used in tests."""

    def __init__(self):
        self.persist = None
        self.called = {}

    def set_persistant_connection(self, value):
        self.persist = value

    async def ping(self):
        self.called["ping"] = self.called.get("ping", 0) + 1
        return "PONG"

    async def version(self):
        self.called["version"] = self.called.get("version", 0) + 1
        return "ClamAV 1.2.3"

    async def stats(self):
        self.called["stats"] = self.called.get("stats", 0) + 1
        return "STATS"

    async def scan(self, path):
        self.called["scan"] = path
        return "OK"

    async def contscan(self, path):
        self.called["contscan"] = path
        return "OK"

    async def instream(self, data):
        self.called["instream"] = data
        return "OK"


@pytest.fixture
def conf():
    return SimpleNamespace(
        CLAMD_CONN="net",
        CLAMD_HOST="127.0.0.1",
        CLAMD_PORT=3310,
        CLAMD_SOCKET="/tmp/clamd.sock",
    )


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_set_logger(conf):
    clam = ClamAv(conf)
    logger = DummyLogger()
    clam.set_logger(logger)
    assert clam.logger is logger


@pytest.mark.anyio
async def test_connecting_uses_network_when_net(monkeypatch, conf):
    fake = FakePVS()

    async def fake_network(host, port):
        assert host == conf.CLAMD_HOST
        assert port == conf.CLAMD_PORT
        return fake

    clam = ClamAv(conf)
    clam.set_logger(DummyLogger())
    monkeypatch.setattr("src.clamav.PyvalveNetwork", fake_network)

    await clam.connecting()

    assert clam.pvs is fake
    assert fake.persist is True


@pytest.mark.anyio
async def test_connecting_uses_socket_when_not_net(monkeypatch, conf):
    fake = FakePVS()
    conf.CLAMD_CONN = "socket"

    async def fake_socket(path):
        assert path == conf.CLAMD_SOCKET
        return fake

    clam = ClamAv(conf)
    clam.set_logger(DummyLogger())
    monkeypatch.setattr("src.clamav.PyvalveSocket", fake_socket)

    await clam.connecting()

    assert clam.pvs is fake
    assert fake.persist is True


@pytest.mark.anyio
async def test_check_connect_connects_on_connection_error(monkeypatch, conf):
    class BrokenPVS:
        async def ping(self):
            raise PyvalveConnectionError()

    clam = ClamAv(conf)
    clam.set_logger(DummyLogger())
    clam.pvs = BrokenPVS()

    calls = {"count": 0}

    async def fake_connecting():
        calls["count"] += 1

    monkeypatch.setattr(clam, "connecting", fake_connecting)

    await clam.check_connect()

    assert calls["count"] == 1


@pytest.mark.anyio
async def test_check_connect_connects_on_attribute_error(monkeypatch, conf):
    clam = ClamAv(conf)
    clam.set_logger(DummyLogger())
    clam.pvs = None

    calls = {"count": 0}

    async def fake_connecting():
        calls["count"] += 1

    monkeypatch.setattr(clam, "connecting", fake_connecting)

    await clam.check_connect()

    assert calls["count"] == 1


@pytest.mark.anyio
async def test_check_connect_no_connect_when_ping_ok(monkeypatch, conf):
    clam = ClamAv(conf)
    clam.set_logger(DummyLogger())
    clam.pvs = FakePVS()

    calls = {"count": 0}

    async def fake_connecting():
        calls["count"] += 1

    monkeypatch.setattr(clam, "connecting", fake_connecting)

    await clam.check_connect()

    assert calls["count"] == 0


@pytest.mark.anyio
async def test_ping_calls_check_connect_and_pvs_ping(monkeypatch, conf):
    clam = ClamAv(conf)
    clam.set_logger(DummyLogger())
    clam.pvs = FakePVS()

    calls = {"count": 0}

    async def fake_check_connect():
        calls["count"] += 1

    monkeypatch.setattr(clam, "check_connect", fake_check_connect)

    result = await clam.ping()

    assert calls["count"] == 1
    assert result == "PONG"


@pytest.mark.anyio
async def test_version_calls_underlying_version(monkeypatch, conf):
    clam = ClamAv(conf)
    clam.set_logger(DummyLogger())
    clam.pvs = FakePVS()

    async def fake_check_connect():
        return None

    monkeypatch.setattr(clam, "check_connect", fake_check_connect)

    result = await clam.version()

    assert result == "ClamAV 1.2.3"
    assert clam.pvs.called["version"] == 1


@pytest.mark.anyio
async def test_stats_calls_underlying_stats(monkeypatch, conf):
    clam = ClamAv(conf)
    clam.set_logger(DummyLogger())
    clam.pvs = FakePVS()

    async def fake_check_connect():
        return None

    monkeypatch.setattr(clam, "check_connect", fake_check_connect)

    result = await clam.stats()

    assert result == "STATS"
    assert clam.pvs.called["stats"] == 1


@pytest.mark.anyio
async def test_scan_calls_underlying_scan(monkeypatch, conf):
    clam = ClamAv(conf)
    clam.set_logger(DummyLogger())
    clam.pvs = FakePVS()

    async def fake_check_connect():
        return None

    monkeypatch.setattr(clam, "check_connect", fake_check_connect)

    result = await clam.scan("/tmp/file.txt")

    assert result == "OK"
    assert clam.pvs.called["scan"] == "/tmp/file.txt"


@pytest.mark.anyio
async def test_contscan_calls_underlying_contscan(monkeypatch, conf):
    clam = ClamAv(conf)
    clam.set_logger(DummyLogger())
    clam.pvs = FakePVS()

    async def fake_check_connect():
        return None

    monkeypatch.setattr(clam, "check_connect", fake_check_connect)

    result = await clam.contscan("/tmp/dir")

    assert result == "OK"
    assert clam.pvs.called["contscan"] == "/tmp/dir"


@pytest.mark.anyio
async def test_instream_calls_underlying_instream(monkeypatch, conf):
    clam = ClamAv(conf)
    clam.set_logger(DummyLogger())
    clam.pvs = FakePVS()

    async def fake_check_connect():
        return None

    monkeypatch.setattr(clam, "check_connect", fake_check_connect)

    payload = b"abc"
    result = await clam.instream(payload)

    assert result == "OK"
    assert clam.pvs.called["instream"] == payload
