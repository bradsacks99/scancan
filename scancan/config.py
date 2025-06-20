""" Config File """
import os

SCAN_CAN_VERSION = "0.1.0"
UPLOAD_SIZE_LIMIT = 104857600
CLAMD_CONN = os.environ.get('CLAMD_CONN', "net")  # 'net' or 'socket'
CLAMD_SOCKET = os.environ.get('CLAMD_SOCKET', "/tmp/clamd.socket")
CLAMD_HOST = os.environ.get('CLAMD_HOST', "lab3.local")
CLAMD_PORT = int(os.environ.get('CLAMD_PORT', 3310))
USE_AUTHENTICATION = os.getenv("USE_AUTHENTICATION", "false").lower() == "true"
