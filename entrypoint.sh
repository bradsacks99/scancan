#! /usr/bin/bash

#echo "Starting Freshclamd"
#freshclam 

echo "Starting Clamd"
clamd &

uvicorn main:app --host 0.0.0.0 --port 8080