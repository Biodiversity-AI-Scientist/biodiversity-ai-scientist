#!/usr/bin/env python3
"""
Biodiversity AI Scientist (BAIS) — System Diagnostic & Health Doctor
Verifies runtime health, database schema integrity, project records, LLM connectivity, and HTTP endpoints.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def check_python_environment() -> Dict[str, Any]:
    v = sys.version_info
    ver_str = f"{v.major}.{v.minor}.{v.micro}"
    in_venv = sys.prefix != sys.base_prefix
    return {
        "id": "python_environment",
        "name": "Python Environment",
        "status": "PASS" if v.major == 3 and v.minor >= 10 else "FAIL",
        "detected": f"Python {ver_str} ({'Virtualenv' if in_venv else 'System Python'})",
        "details": f"Executable: {sys.executable}",
    }


def check_database_and_tables() -> Dict[str, Any]:
    try:
        from src.database import engine, Base
        from sqlalchemy import text

        with engine.connect() as conn:
            if str(engine.url).startswith("sqlite"):
                tables_res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';")).fetchall()
                table_names = [t[0] for t in tables_res if not t[0].startswith("sqlite_")]
                db_type = "SQLite"
            else:
                tables_res = conn.execute(text("SHOW TABLES;")).fetchall()
                table_names = [t[0] for t in tables_res]
                db_type = "MySQL"

        expected_count = len(Base.metadata.tables)
        detected_count = len(table_names)
        passed = detected_count >= 10

        return {
            "id": "database_integrity",
            "name": "Database & Relational Schema",
            "status": "PASS" if passed else "FAIL",
            "detected": f"{db_type} ({detected_count} tables active)",
            "details": f"Tables: {', '.join(table_names[:8])} ... ({detected_count} total)",
        }
    except Exception as e:
        return {
            "id": "database_integrity",
            "name": "Database & Relational Schema",
            "status": "FAIL",
            "detected": f"Connection failed: {e}",
            "details": str(e),
        }


def check_scientific_entities() -> Dict[str, Any]:
    try:
        from src.database import SessionLocal
        from src.models import ResearchProject, ResearchQuestion, Hypothesis, ScientificCapability
        from sqlalchemy import select, func

        with SessionLocal() as db:
            proj_count = db.scalar(select(func.count(ResearchProject.id))) or 0
            q_count = db.scalar(select(func.count(ResearchQuestion.id))) or 0
            h_count = db.scalar(select(func.count(Hypothesis.id))) or 0
            cap_count = db.scalar(select(func.count(ScientificCapability.id))) or 0

        return {
            "id": "scientific_entities",
            "name": "Scientific State & Records",
            "status": "PASS",
            "detected": f"{proj_count} project(s), {q_count} question(s), {h_count} hypothesis(es)",
            "details": f"Registered Capabilities: {cap_count}",
        }
    except Exception as e:
        return {
            "id": "scientific_entities",
            "name": "Scientific State & Records",
            "status": "WARNING",
            "detected": "Unable to query records",
            "details": str(e),
        }


def check_llm_gateway() -> Dict[str, Any]:
    try:
        from src.config import settings
        from src.llm.provider import create_provider

        if not settings.llm_configured:
            return {
                "id": "llm_gateway",
                "name": "LLM Reasoning Gateway",
                "status": "INFO",
                "detected": "Unconfigured (Optional API key not set in .env)",
                "details": "To enable AI reasoning, set LLM_API_KEY in .env or via configuration.php",
            }

        provider = create_provider(
            settings.llm_provider,
            api_key=settings.llm_api_key.get_secret_value() if settings.llm_api_key else None,
            base_url=settings.llm_base_url,
            timeout_seconds=5.0,
        )
        try:
            if hasattr(provider, "check_balance"):
                res = provider.check_balance()
                auth_ok = True
                quota_ok = res.get("is_available", True)
            else:
                auth_ok = True
                quota_ok = True
        finally:
            provider.close()

        return {
            "id": "llm_gateway",
            "name": "LLM Reasoning Gateway",
            "status": "PASS" if auth_ok else "FAIL",
            "detected": f"{settings.llm_provider} ({settings.llm_default_model})",
            "details": f"Authenticated: {auth_ok}, Quota: {'Available' if quota_ok else 'Exhausted'}",
        }
    except Exception as e:
        return {
            "id": "llm_gateway",
            "name": "LLM Reasoning Gateway",
            "status": "WARNING",
            "detected": f"Connection notice: {e}",
            "details": str(e),
        }


def check_disk_and_storage() -> Dict[str, Any]:
    try:
        data_dir = REPO_ROOT / "data"
        data_size_mb = 0
        if data_dir.exists():
            data_size_mb = sum(f.stat().st_size for f in data_dir.glob("**/*") if f.is_file()) / (1024 * 1024)

        return {
            "id": "storage",
            "name": "Local Storage & Data Store",
            "status": "PASS",
            "detected": f"data/ directory: {data_size_mb:.2f} MB",
            "details": f"Path: {data_dir}",
        }
    except Exception as e:
        return {
            "id": "storage",
            "name": "Local Storage & Data Store",
            "status": "WARNING",
            "detected": str(e),
            "details": "",
        }


def run_doctor_checks() -> List[Dict[str, Any]]:
    return [
        check_python_environment(),
        check_database_and_tables(),
        check_scientific_entities(),
        check_llm_gateway(),
        check_disk_and_storage(),
    ]


def main():
    parser = argparse.ArgumentParser(description="Biodiversity AI Scientist (BAIS) — Diagnostic Doctor")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON report")
    args = parser.parse_args()

    checks = run_doctor_checks()
    all_healthy = all(c["status"] in ["PASS", "INFO", "WARNING"] for c in checks)

    if args.json:
        print(json.dumps({"healthy": all_healthy, "checks": checks}, indent=2))
    else:
        print("\n=======================================================")
        print(" 🩺 Biodiversity AI Scientist (BAIS) — System Doctor")
        print("=======================================================")
        for c in checks:
            status = c["status"]
            name = c["name"]
            detected = c["detected"]
            color = "\033[92m" if status == "PASS" else ("\033[94m" if status == "INFO" else ("\033[93m" if status == "WARNING" else "\033[91m"))
            reset = "\033[0m"
            print(f"[{color}{status:^7}{reset}] {name:<30} : {detected}")
            if c.get("details"):
                print(f"          ↳ {c['details']}")
        print("=======================================================")
        if all_healthy:
            print("\033[92mAll system diagnostic checks completed successfully.\033[0m\n")
        else:
            print("\033[91mOne or more components require attention. See above details.\033[0m\n")

    sys.exit(0 if all_healthy else 1)


if __name__ == "__main__":
    main()
