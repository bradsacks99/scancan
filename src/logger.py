"""ScanCan Logger"""
import logging
import sys

from config import LOG_FORMAT, LOG_LEVEL


class Logger:
    """Logger"""
    def __init__(self, name: str = 'ScanCan') -> None:
        """
        Logger constructor

            Parameters:
                name (String): A logger name

            Returns:
                None
        """
        self.logger = logging.getLogger(name)
        self.level = LOG_LEVEL
        self.format = LOG_FORMAT

    def set_level(self, level) -> None:
        """ Set logger level"""
        self.level = level

    def set_format(self, log_format) -> None:
        """ Set logger format"""
        self.format = log_format

    def get_logger(self) -> logging.Logger:
        """
        Get Logger

            Returns:
                logger (Logger)
        """
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter(self.format)
        con = logging.StreamHandler(stream=sys.stdout)
        con.setLevel(level=logging.INFO)
        con.setFormatter(formatter)
        self.logger.addHandler(con)

        return self.logger
