#!/usr/bin/env python3
"""
Biodiversity AI Scientist (BAIS) — Canonical Public Installer
Automates environment setup, dependency resolution, configuration, and database initialization.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Ensure install directory is in path for preflight import
INSTALL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(INSTALL_DIR))

from preflight import run_all_preflights


class InstallationError(Exception):
    pass


def run_command(
    cmd: list[str],
    cwd: Path,
    env: Optional[Dict[str, str]] = None,
    timeout: int = 180,
) -> Tuple[int, str, str]:
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            env=full_env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        raise InstallationError(f"Command '{' '.join(cmd)}' timed out after {timeout}s")
    except Exception as e:
        raise InstallationError(f"Command execution error: {e}")


def install_bais(
    repo_root: Path,
    port: int = 8000,
    host: str = "127.0.0.1",
    db_url: Optional[str] = None,
    venv_dir_name: str = ".venv",
    skip_deps: bool = False,
    progress_callback: Optional[callable] = None,
) -> Dict[str, Any]:
    """
    Executes the canonical BAIS installation workflow in repo_root.
    """
    start_time = time.time()
    steps_log: Dict[str, Any] = {}

    def log_step(name: str, passed: bool, details: str = ""):
        steps_log[name] = {"passed": passed, "details": details}
        if progress_callback:
            progress_callback(name, passed, details)

    # 1. Preflight Validation
    all_passed, preflight_checks = run_all_preflights(repo_root, port=port, host=host)
    log_step(
        "preflight",
        all_passed,
        f"{sum(1 for c in preflight_checks if c['status'] == 'PASS')}/{len(preflight_checks)} checks passed",
    )
    if not all_passed:
        failed = [c["name"] for c in preflight_checks if c["status"] == "FAIL"]
        raise InstallationError(f"Preflight validation failed: {', '.join(failed)}")

    # 2. Virtual Environment Setup
    venv_dir = (repo_root / venv_dir_name).resolve()
    python_bin = venv_dir / ("Scripts" if os.name == "nt" else "bin") / "python"
    pip_bin = venv_dir / ("Scripts" if os.name == "nt" else "bin") / "pip"

    if not venv_dir.exists():
        import venv
        try:
            venv.create(venv_dir, with_pip=True)
            log_step("virtualenv", True, f"Created isolated virtual environment at '{venv_dir}'")
        except Exception as e:
            log_step("virtualenv", False, str(e))
            raise InstallationError(f"Failed to create virtual environment: {e}")
    else:
        log_step("virtualenv", True, f"Using existing virtual environment at '{venv_dir}'")

    # 3. Dependency Installation
    reqs_file = repo_root / "requirements.txt"
    if not skip_deps and reqs_file.exists() and reqs_file.stat().st_size > 0:
        code, out, err = run_command([str(pip_bin), "install", "-r", str(reqs_file)], cwd=repo_root, timeout=300)
        if code != 0:
            log_step("dependencies", False, f"pip install failed:\n{err}")
            raise InstallationError(f"Dependency installation failed: {err}")
        log_step("dependencies", True, "All requirements installed successfully.")
    else:
        log_step("dependencies", True, "Skipped dependency installation (cached or empty requirements).")

    # 4. Environment Configuration
    data_dir = repo_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    chosen_db_url = db_url or f"sqlite:///{data_dir.as_posix()}/bais_database.db"
    env_content = f"""# Biodiversity AI Scientist (BAIS) — Runtime Configuration
APP_PORT={port}
DATABASE_URL={chosen_db_url}

# Generic LLM Gateway Settings (Disabled by default in public release)
LLM_GATEWAY_ENABLED=false
LLM_PROVIDER=openai_responses
LLM_BASE_URL=https://api.openai.com/v1
"""
    env_file = repo_root / ".env"
    if not env_file.exists():
        env_file.write_text(env_content)
        try:
            os.chmod(env_file, 0o644)
        except Exception:
            pass
        log_step("configuration", True, f"Generated runtime configuration with database '{chosen_db_url}'")
    else:
        log_step("configuration", True, f"Existing configuration preserved at '{env_file}'")

    # 5. Database Schema Initialization
    init_db_script = f"""
import os
import sys
sys.path.insert(0, '{repo_root.as_posix()}')

from src.database import Base, engine
import src.models

try:
    Base.metadata.create_all(engine)
    print("DATABASE_INITIALIZED_SUCCESSFULLY")
except Exception as e:
    print(f"DATABASE_INIT_ERROR: {{e}}")
    sys.exit(1)
"""
    code, out, err = run_command(
        [str(python_bin), "-c", init_db_script],
        cwd=repo_root,
        env={"DATABASE_URL": chosen_db_url},
    )
    if code != 0 or "DATABASE_INITIALIZED_SUCCESSFULLY" not in out:
        log_step("database_init", False, f"Database table initialization failed:\n{err}\n{out}")
        raise InstallationError(f"Database initialization failed: {err or out}")
    log_step("database_init", True, "Database schema initialized successfully.")

    # 6. Smoke Test (App Import Check)
    smoke_script = f"""
import os
import sys
sys.path.insert(0, '{repo_root.as_posix()}')
from src.main import app
assert app.title == "Biodiversity AI Scientist"
print("SMOKE_TEST_PASSED")
"""
    code, out, err = run_command([str(python_bin), "-c", smoke_script], cwd=repo_root)
    if code != 0 or "SMOKE_TEST_PASSED" not in out:
        log_step("smoke_test", False, f"Smoke test failed:\n{err}")
        raise InstallationError(f"Application import smoke test failed: {err}")
    log_step("smoke_test", True, "FastAPI application loaded successfully.")

    elapsed = time.time() - start_time
    return {
        "success": True,
        "repo_root": str(repo_root),
        "port": port,
        "host": host,
        "venv_dir": str(venv_dir),
        "python_bin": str(python_bin),
        "database_url": chosen_db_url,
        "elapsed_seconds": round(elapsed, 2),
        "steps": steps_log,
        "preflight_checks": preflight_checks,
    }


def main():
    parser = argparse.ArgumentParser(description="Biodiversity AI Scientist (BAIS) Public Installer")
    parser.add_argument("--dir", default=".", help="Target repository directory (default: .)")
    parser.add_argument("--port", type=int, default=8000, help="Target application port (default: 8000)")
    parser.add_argument("--host", default="127.0.0.1", help="Binding host (default: 127.0.0.1)")
    parser.add_argument("--db-url", default=None, help="Custom SQLAlchemy database URL (default: sqlite:///data/bais_database.db)")
    parser.add_argument("--venv-dir", default=".venv", help="Name or path of virtual environment directory (default: .venv)")
    parser.add_argument("--skip-deps", action="store_true", help="Skip pip dependency installation")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON result")
    args = parser.parse_args()

    repo_root = Path(args.dir).resolve()

    if not args.json:
        print("\n=======================================================")
        print(" Biodiversity AI Scientist (BAIS) Public Installer")
        print("=======================================================")
        print(f"Target directory: {repo_root}")
        print(f"Configured port : {args.port}")
        print(f"Configured host : {args.host}")
        print("-------------------------------------------------------")

    try:
        res = install_bais(
            repo_root=repo_root,
            port=args.port,
            host=args.host,
            db_url=args.db_url,
            venv_dir_name=args.venv_dir,
            skip_deps=args.skip_deps,
        )

        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print("\nInstallation completed successfully in", res["elapsed_seconds"], "seconds!")
            print("To start Biodiversity AI Scientist:")
            print(f"  cd {repo_root}")
            print(f"  source {res['venv_dir']}/bin/activate")
            print(f"  uvicorn src.main:app --host {args.host} --port {args.port}")
            print("=======================================================\n")
        sys.exit(0)

    except InstallationError as e:
        if args.json:
            print(json.dumps({"success": False, "error": str(e)}, indent=2))
        else:
            print(f"\n\033[91mInstallation Failed: {e}\033[0m\n")
        sys.exit(1)
    except Exception as e:
        if args.json:
            print(json.dumps({"success": False, "error": str(e)}, indent=2))
        else:
            print(f"\n\033[91mUnexpected Error: {e}\033[0m\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
