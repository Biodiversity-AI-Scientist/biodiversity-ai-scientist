#!/usr/bin/env python3
"""
Biodiversity AI Scientist (BAIS) — One-Click Quick Launcher
Detects isolated runtime environment, configures ports, and launches FastAPI.
"""

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
os.chdir(REPO_ROOT)

venv_bin = REPO_ROOT / ".venv" / ("Scripts" if os.name == "nt" else "bin")
python_bin = venv_bin / "python"
uvicorn_bin = venv_bin / "uvicorn"

if not venv_bin.exists():
    print("Virtual environment not found. Running public installer...")
    code = subprocess.run([sys.executable, str(REPO_ROOT / "install" / "install.py")]).returncode
    if code != 0:
        sys.exit(code)

port = int(os.environ.get("APP_PORT", 8000))
host = os.environ.get("APP_HOST", "0.0.0.0")

print("\n" + "=" * 65)
print(" 🚀 Biodiversity AI Scientist is starting...")
print(f" 👉 Web Interface : http://localhost:{port}/ai-scientist/")
print(f" 👉 PRM Manager   : http://localhost:{port}/bais_prm/")
print(f" 👉 API Docs      : http://localhost:{port}/docs")
print("=" * 65 + "\n")

cmd = [str(python_bin), "-m", "uvicorn", "src.main:app", "--host", host, "--port", str(port)]
os.execv(str(python_bin), cmd)
