#!/bin/bash
set -e

echo "[entrypoint] Running database migrations..."
alembic upgrade head

echo "[entrypoint] Starting application on 0.0.0.0:8000..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
