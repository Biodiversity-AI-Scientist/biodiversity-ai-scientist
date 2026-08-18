#!/usr/bin/env python3
"""
Biodiversity AI Scientist (BAIS) — Preflight & Prerequisite Validator
Validates runtime environment, tools, and resources prior to installation.
"""

import argparse
import json
import os
import platform
import shutil
import socket
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


def check_os() -> Dict[str, Any]:
    sys_name = platform.system()
    machine = platform.machine()
    supported = sys_name in ["Linux", "Darwin"]
    return {
        "id": "os",
        "name": "Operating System",
        "status": "PASS" if supported else "WARNING",
        "mandatory": True,
        "detected": f"{sys_name} ({machine})",
        "required": "Linux / macOS / POSIX",
        "message": "Supported operating system detected." if supported else f"Untested operating system: {sys_name}.",
        "remediation": "Deploy on Ubuntu 22.04+, Debian 12+, or macOS." if not supported else None,
    }


def check_python_version() -> Dict[str, Any]:
    v = sys.version_info
    ver_str = f"{v.major}.{v.minor}.{v.micro}"
    passed = (v.major == 3 and v.minor >= 10)
    return {
        "id": "python_version",
        "name": "Python Version",
        "status": "PASS" if passed else "FAIL",
        "mandatory": True,
        "detected": ver_str,
        "required": ">= 3.10",
        "message": f"Python {ver_str} meets version requirements." if passed else f"Python {ver_str} is below required 3.10+.",
        "remediation": "Install Python 3.10, 3.11, or 3.12 (e.g. `apt-get install python3.12 python3.12-venv`)." if not passed else None,
    }


def check_venv_support() -> Dict[str, Any]:
    try:
        import venv
        passed = True
        msg = "Python `venv` standard library module is available."
        remediation = None
    except ImportError:
        passed = False
        msg = "Python `venv` module is missing."
        remediation = "Install the venv package for your Python version (e.g. `sudo apt install python3-venv`)."

    return {
        "id": "python_venv",
        "name": "Python venv Module",
        "status": "PASS" if passed else "FAIL",
        "mandatory": True,
        "detected": "Available" if passed else "Missing",
        "required": "Python venv module",
        "message": msg,
        "remediation": remediation,
    }


def check_git() -> Dict[str, Any]:
    git_path = shutil.which("git")
    if git_path:
        return {
            "id": "git",
            "name": "Git Command Line",
            "status": "PASS",
            "mandatory": False,
            "detected": f"Found at {git_path}",
            "required": "git executable",
            "message": "Git is installed and available in PATH.",
            "remediation": None,
        }
    return {
        "id": "git",
        "name": "Git Command Line",
        "status": "WARNING",
        "mandatory": False,
        "detected": "Not in PATH",
        "required": "git executable",
        "message": "Git binary was not found in PATH.",
        "remediation": "Install git (`sudo apt install git`).",
    }


def check_disk_space(target_path: Path, min_mb: int = 500) -> Dict[str, Any]:
    try:
        stat = shutil.disk_usage(str(target_path.resolve()))
        free_mb = stat.free / (1024 * 1024)
        free_gb = free_mb / 1024
        passed = free_mb >= min_mb
        return {
            "id": "disk_space",
            "name": "Available Disk Space",
            "status": "PASS" if passed else "FAIL",
            "mandatory": True,
            "detected": f"{free_gb:.1f} GB free",
            "required": f">= {min_mb} MB",
            "message": f"Sufficient disk space available ({free_gb:.1f} GB)." if passed else f"Insufficient disk space ({free_mb:.0f} MB free, {min_mb} MB required).",
            "remediation": "Free up disk space on target partition." if not passed else None,
        }
    except Exception as e:
        return {
            "id": "disk_space",
            "name": "Available Disk Space",
            "status": "WARNING",
            "mandatory": False,
            "detected": "Unknown",
            "required": f">= {min_mb} MB",
            "message": f"Could not determine free disk space: {e}",
            "remediation": None,
        }


def check_port_availability(port: int, host: str = "127.0.0.1") -> Dict[str, Any]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((host, port))
        sock.close()
        return {
            "id": "port_availability",
            "name": f"Port {port} Availability",
            "status": "PASS",
            "mandatory": True,
            "detected": f"Port {port} is free",
            "required": f"Port {port} bindable on {host}",
            "message": f"TCP port {port} is available for binding.",
            "remediation": None,
        }
    except OSError as e:
        return {
            "id": "port_availability",
            "name": f"Port {port} Availability",
            "status": "FAIL",
            "mandatory": True,
            "detected": f"Port {port} is occupied / cannot bind ({e.strerror})",
            "required": f"Port {port} bindable on {host}",
            "message": f"Port {port} is currently in use by another process.",
            "remediation": f"Select an alternative port (e.g. {port + 1}) or stop the occupying process.",
        }


def check_filesystem_writable(target_dir: Path) -> Dict[str, Any]:
    test_file = target_dir / ".bais_write_test"
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        test_file.write_text("test_ok")
        test_file.unlink()
        return {
            "id": "filesystem_writable",
            "name": "Filesystem Permissions",
            "status": "PASS",
            "mandatory": True,
            "detected": "Directory writable",
            "required": "Read/Write permissions",
            "message": f"Target directory '{target_dir}' is writable.",
            "remediation": None,
        }
    except Exception as e:
        return {
            "id": "filesystem_writable",
            "name": "Filesystem Permissions",
            "status": "FAIL",
            "mandatory": True,
            "detected": f"Write failed: {e}",
            "required": "Read/Write permissions",
            "message": f"Cannot write to directory '{target_dir}'.",
            "remediation": f"Ensure current user has write permissions to '{target_dir}'.",
        }


def run_all_preflights(
    target_dir: Path,
    port: int = 8000,
    host: str = "127.0.0.1",
) -> Tuple[bool, List[Dict[str, Any]]]:
    checks = [
        check_os(),
        check_python_version(),
        check_venv_support(),
        check_git(),
        check_disk_space(target_dir),
        check_filesystem_writable(target_dir),
        check_port_availability(port, host=host),
    ]

    all_passed = all(
        c["status"] == "PASS" or not c.get("mandatory", False)
        for c in checks
    )

    return all_passed, checks


def main():
    parser = argparse.ArgumentParser(description="BAIS Installation Preflight Validator")
    parser.add_argument("--dir", default=".", help="Target installation directory (default: .)")
    parser.add_argument("--port", type=int, default=8000, help="Target application TCP port (default: 8000)")
    parser.add_argument("--host", default="127.0.0.1", help="Binding host interface (default: 127.0.0.1)")
    parser.add_argument("--json", action="store_true", help="Output results formatted as JSON")
    args = parser.parse_args()

    target_dir = Path(args.dir).resolve()
    all_passed, checks = run_all_preflights(target_dir, port=args.port, host=args.host)

    if args.json:
        print(json.dumps({"all_passed": all_passed, "target_dir": str(target_dir), "checks": checks}, indent=2))
    else:
        print("\n=======================================================")
        print(" Biodiversity AI Scientist — Preflight Check Report")
        print("=======================================================")
        for c in checks:
            status = c["status"]
            name = c["name"]
            detected = c["detected"]
            color = "\033[92m" if status == "PASS" else ("\033[93m" if status == "WARNING" else "\033[91m")
            reset = "\033[0m"
            print(f"[{color}{status:^7}{reset}] {name:<26} : {detected}")
            if status == "FAIL" and c.get("remediation"):
                print(f"          ↳ Remediation: {c['remediation']}")
        print("=======================================================")
        if all_passed:
            print("\033[92mAll mandatory preflight checks passed successfully.\033[0m\n")
        else:
            print("\033[91mPreflight checks failed. Please resolve above issues.\033[0m\n")

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
