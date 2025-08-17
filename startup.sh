#!/usr/bin/env bash

set -e

# Simple startup for backend-only
export ENVIRONMENT=${ENVIRONMENT:-development}
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-8000}

cd "$(dirname "$0")"

# Create data dir
mkdir -p data

# Install backend requirements
python3 -m pip install --break-system-packages -q -r backend/requirements.txt || true

# Run backend
cd backend
exec python3 main.py