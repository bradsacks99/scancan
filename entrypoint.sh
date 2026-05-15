#! /bin/bash

#echo "Starting Freshclamd"
#freshclam 

echo "Starting Clamd"
clamd &

echo "Waiting for Clamd socket"
python3 - <<'PY'
import socket
import time
import sys

socket_path = "/var/run/clamav/clamd.ctl"

for _ in range(60):
	try:
		with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
			client.settimeout(1)
			client.connect(socket_path)
			client.sendall(b"PING\n")
			response = client.recv(1024).decode("utf-8", "replace")
			if "PONG" in response:
				sys.exit(0)
	except OSError:
		time.sleep(1)

raise SystemExit("clamd socket not ready")
PY

echo "Starting API Service"
uvicorn main:app --host 0.0.0.0 --port 8080