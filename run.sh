#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Running public installer..."
    python3 install/install.py
fi

source .venv/bin/activate
PORT=${APP_PORT:-8000}
HOST=${APP_HOST:-0.0.0.0}

echo ""
echo "==============================================================="
echo " 🚀 Biodiversity AI Scientist is starting..."
echo " 👉 Web Interface : http://localhost:${PORT}/ai-scientist/"
echo " 👉 PRM Manager   : http://localhost:${PORT}/bais_prm/"
echo " 👉 API Docs      : http://localhost:${PORT}/docs"
echo "==============================================================="
echo ""

exec uvicorn src.main:app --host "$HOST" --port "$PORT"
