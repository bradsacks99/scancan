""" Config File """
import os

upload_size_limit = 104857600
clamd_conn = os.environ.get('CLAMD_CONN', "net")  # 'net' or 'socket'
clamd_socket = "/tmp/clamd.socket"
clamd_host = "10.0.5.146"
clamd_port = 3310
