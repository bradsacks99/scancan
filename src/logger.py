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
        level = getattr(logging, self.level, logging.INFO)
        self.logger.setLevel(level)
        formatter = logging.Formatter(self.format)
        con = logging.StreamHandler(stream=sys.stdout)
        con.setLevel(level=level)
        con.setFormatter(formatter)

        # Avoid duplicate stream handlers if get_logger is called repeatedly.
        has_stdout_handler = any(
            isinstance(handler, logging.StreamHandler)
            and getattr(handler, "stream", None) is sys.stdout
            for handler in self.logger.handlers
        )
        if not has_stdout_handler:
            self.logger.addHandler(con)

        return self.logger
