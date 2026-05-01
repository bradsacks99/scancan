"""Tests for src/utils.py"""

import pytest

from src.utils import get_clamav_connection


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_get_clamav_connection_sets_persistent_and_returns_socket(monkeypatch):
    calls = {"created": 0}

    class FakeSocket:
        def __init__(self):
            self.persistent = None

        def set_persistant_connection(self, value):
            self.persistent = value

    fake_socket = FakeSocket()

    async def fake_pyvalve_socket(*args, **kwargs):
        assert args == ()
        assert kwargs == {}
        calls["created"] += 1
        return fake_socket

    monkeypatch.setattr("src.utils.PyvalveSocket", fake_pyvalve_socket)

    result = await get_clamav_connection()

    assert calls["created"] == 1
    assert result is fake_socket
    assert fake_socket.persistent is True
