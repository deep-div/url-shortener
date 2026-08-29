#!/bin/sh
set -e

echo "Starting backend..."
cd /app/backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 &

echo "Starting nginx (static frontend server)..."
# binary at /usr/local/bin/nginx which shadows the real apt-installed
# nginx at /usr/sbin/nginx earlier in $PATH.
/usr/sbin/nginx -g "daemon off;" &

echo "Waiting for nginx to be ready..."
until curl -sf http://127.0.0.1:3000/ -o /dev/null; do sleep 0.5; done

echo "Waiting for backend to be ready..."
until curl -sf http://127.0.0.1:8000/health -o /dev/null; do sleep 0.5; done

echo "Starting Kong (API gateway)..."
kong start &

# Wait for all background processes
wait
