"""
Permanent Invariant Tests for Private Infrastructure Decoupling.

Guarantees that generic BAIS core production code contains NO hardcoded
private RFC 1918 IP addresses (192.168.x.x, 10.x.x.x, 172.16-31.x.x)
or private deployment hostnames, and that generic services
function gracefully without private environment variables configured.
"""
import os
import re
from pathlib import Path
import pytest

from src.config import Settings
from src.services.domain_intelligence import search_local_papers_library
from src.services.research_program import (
    get_findshell_publications_index,
    search_papers_api,
)


class TestPrivateInfrastructureBoundary:
    PRIVATE_IP_PATTERN = re.compile(
        r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
        r"172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|"
        r"192\.168\.\d{1,3}\.\d{1,3})\b"
    )
    _TARGET_SERVER_PREFIX = "server"
    _TARGET_SERVER_NUM = "94"
    PRIVATE_HOST_PATTERN = re.compile(
        rf"\b{_TARGET_SERVER_PREFIX}{_TARGET_SERVER_NUM}(?:\.local)?\b",
        re.IGNORECASE,
    )

    def test_01_generic_src_contains_zero_private_ips(self):
        """Verify no RFC 1918 private IP literals exist in generic source code."""
        src_root = Path(__file__).resolve().parent.parent / "src"
        violations = []

        for py_file in src_root.rglob("*.py"):
            # Exclude private integration modules
            if "integrations" in py_file.parts:
                continue

            content = py_file.read_text(encoding="utf-8")
            for lineno, line in enumerate(content.splitlines(), start=1):
                # Ignore test fixture markers or comment-only doc references if any
                matches = self.PRIVATE_IP_PATTERN.findall(line)
                if matches:
                    rel = py_file.relative_to(src_root.parent).as_posix()
                    violations.append(f"{rel}:{lineno}: {matches} in '{line.strip()}'")

        assert len(violations) == 0, (
            f"Found {len(violations)} private IP address literals in generic source:\n"
            + "\n".join(violations)
        )

    def test_02_generic_src_contains_zero_server_identifiers(self):
        """Verify no private server identifiers exist in generic source code."""
        src_root = Path(__file__).resolve().parent.parent / "src"
        violations = []

        for py_file in src_root.rglob("*.py"):
            if "integrations" in py_file.parts:
                continue

            content = py_file.read_text(encoding="utf-8")
            for lineno, line in enumerate(content.splitlines(), start=1):
                matches = self.PRIVATE_HOST_PATTERN.findall(line)
                if matches:
                    rel = py_file.relative_to(src_root.parent).as_posix()
                    violations.append(f"{rel}:{lineno}: {matches} in '{line.strip()}'")

        assert len(violations) == 0, (
            f"Found {len(violations)} private server references in generic source:\n"
            + "\n".join(violations)
        )

    def test_03_settings_default_hosts_are_generic(self):
        """Verify Settings defaults to localhost/generic hosts without private configuration."""
        settings = Settings(
            db_host="localhost",
            db_name="test_db",
            db_user="user",
            db_password="pw",
            _env_file=None,
        )
        assert settings.dwh_db_host == "localhost"
        assert settings.datalake_db_host == "localhost"
        assert not self.PRIVATE_IP_PATTERN.search(settings.dwh_db_host)
        assert not self.PRIVATE_IP_PATTERN.search(settings.datalake_db_host)

    def test_04_generic_services_graceful_when_external_apis_unconfigured(self, monkeypatch):
        """Verify services operate gracefully when optional external services are empty."""
        monkeypatch.delenv("PAPERS_API_URL", raising=False)
        monkeypatch.delenv("FINDSHELL_BLOG_URL", raising=False)

        # Domain intelligence search returns empty list without error
        papers = search_local_papers_library("Cerithioidea", max_results=3)
        assert papers == []

        # Research program papers search returns empty list without error
        api_results = search_papers_api("Mollusca", limit=5)
        assert api_results == []

        # FindShell bibliography returns fallback items with relative URLs
        pubs = get_findshell_publications_index()
        assert len(pubs) > 0
        for pub in pubs:
            assert "url" in pub
            assert not self.PRIVATE_IP_PATTERN.search(pub["url"])
