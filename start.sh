#!/bin/sh
set -e

echo "Starting backend..."
cd /app/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

echo "Serving frontend..."
cd /app/frontend/dist
python3 -m http.server 4000 &

# Wait for any process to exit
wait -n

# Exit with the status of the process that exited first
exit $?
