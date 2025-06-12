""" Config File """
import os

UPLOAD_SIZE_LIMIT = 104857600
clamd_conn = os.environ.get('CLAMD_CONN', "net")  # 'net' or 'socket'
clamd_socket = os.environ.get('CLAMD_SOCKET', "/tmp/clamd.socket")
clamd_host = os.environ.get('CLAMD_HOST', "lab3.local")
clamd_port = int(os.environ.get('CLAMD_PORT', 3310))
