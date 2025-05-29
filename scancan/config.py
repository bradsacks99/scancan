""" Config File """
import os

upload_size_limit = 104857600
clamd_conn = os.environ.get('CLAMD_CONN', "net")  # 'net' or 'socket'
clamd_socket = os.environ.get('CLAMD_SOCKET', "/tmp/clamd.socket")
clamd_host = os.environ.get('CLAMD_HOST', "lab3.local")
clamd_port = os.environ.get('CLAMD_PORT', 3310)
