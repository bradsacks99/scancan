#!/bin/bash
set -e

echo "Running initial freshclam update..."
/usr/bin/freshclam --quiet

echo "Starting cron..."
exec cron -f
