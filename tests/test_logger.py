"""Tests for src/logger.py"""
import importlib
import logging
import sys

import src.logger as logger_module
from src.logger import Logger

# logger.py imports 'config' via the bare name (src/ is in sys.path)
_config_module = sys.modules['config']


def test_get_logger_returns_logging_logger():
    log = Logger(name="test_basic").get_logger()
    assert isinstance(log, logging.Logger)


def test_get_logger_name():
    log = Logger(name="my_app").get_logger()
    assert log.name == "my_app"


def test_get_logger_default_name():
    log = Logger().get_logger()
    assert log.name == "ScanCan"


def test_get_logger_adds_stream_handler():
    log = Logger(name="test_handler").get_logger()
    assert any(isinstance(h, logging.StreamHandler) for h in log.handlers)


def test_get_logger_level():
    log = Logger(name="test_level").get_logger()
    assert log.level == logging.INFO


def test_set_level():
    instance = Logger(name="test_set_level")
    instance.set_level("DEBUG")
    assert instance.level == "DEBUG"


def test_set_format():
    instance = Logger(name="test_set_format")
    fmt = "%(levelname)s %(message)s"
    instance.set_format(fmt)
    assert instance.format == fmt


def test_set_format_applied_to_handler():
    fmt = "%(levelname)s %(message)s"
    instance = Logger(name="test_fmt_handler")
    instance.set_format(fmt)
    log = instance.get_logger()
    stream_handlers = [h for h in log.handlers if isinstance(h, logging.StreamHandler)]
    assert stream_handlers
    assert stream_handlers[-1].formatter._fmt == fmt


def test_default_format_from_config():
    instance = Logger(name="test_default_fmt")
    assert instance.format == _config_module.LOG_FORMAT


def test_default_level_from_config():
    instance = Logger(name="test_default_lvl")
    assert instance.level == _config_module.LOG_LEVEL


def test_log_format_env_override(monkeypatch):
    fmt = "%(levelname)s - %(message)s"
    monkeypatch.setenv("LOG_FORMAT", fmt)
    importlib.reload(_config_module)
    importlib.reload(logger_module)
    instance = logger_module.Logger(name="test_env_fmt")
    assert instance.format == fmt


def test_log_level_env_override(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    importlib.reload(_config_module)
    importlib.reload(logger_module)
    instance = logger_module.Logger(name="test_env_lvl")
    assert instance.level == "WARNING"
