""" Config File """
import os

SCAN_CAN_VERSION: str = "0.1.0"
UPLOAD_SIZE_LIMIT: int = 104857600
CLAMD_CONN: str = os.environ.get('CLAMD_CONN', "net")  # 'net' or 'socket'
CLAMD_SOCKET: str = os.environ.get('CLAMD_SOCKET', "/tmp/clamd.socket")
CLAMD_HOST: str = os.environ.get('CLAMD_HOST', "lab3.local")
CLAMD_PORT: int = int(os.environ.get('CLAMD_PORT', 3310))
USE_AUTHENTICATION: bool = os.getenv("USE_AUTHENTICATION", "false").lower() == "true"
LOG_FORMAT: str = os.getenv("LOG_FORMAT", "%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
