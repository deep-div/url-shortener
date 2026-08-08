#!/bin/sh
set -e

echo "Starting backend..."
cd /app/backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 &

echo "Starting nginx..."
nginx -g "daemon off;" &

# Wait for all background processes
wait
