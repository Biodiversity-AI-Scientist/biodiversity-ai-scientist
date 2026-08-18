"""
Permanent Architectural Invariant Test for R01/B01 Modular Boundary.

Guarantees that Generic BAIS Core code and generic test suites NEVER import
deployment-specific IdentifyShell modules (enforcing the strict dependency
direction: IdentifyShell -> BAIS Core, never BAIS Core -> IdentifyShell).
"""
import ast
from pathlib import Path
import pytest

from src.core.providers.registry import ProviderRegistry


class TestModularIndependence:
    FORBIDDEN_PREFIXES = (
        "src.integrations.identifyshell",
        "src.integrations",
        "identifyshell",
    )

    def test_01_generic_core_contains_zero_identifyshell_imports(self):
        """
        AST-level verification that no generic core module imports private IdentifyShell packages.
        """
        repo_root = Path(__file__).resolve().parent.parent
        src_root = repo_root / "src"

        # Generic core directories to audit
        generic_packages = [
            src_root / "core",
            src_root / "models",
            src_root / "schemas",
            src_root / "services",
            src_root / "repositories",
            src_root / "routers",
            src_root / "executors",
            src_root / "llm",
            src_root / "telemetry",
            src_root / "config.py",
            src_root / "database.py",
            src_root / "main.py",
        ]

        violations = []

        for target in generic_packages:
            files_to_check = [target] if target.is_file() else list(target.rglob("*.py"))
            for py_file in files_to_check:
                if not py_file.is_file():
                    continue

                content = py_file.read_text(encoding="utf-8")
                tree = ast.parse(content, filename=str(py_file))

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            for prefix in self.FORBIDDEN_PREFIXES:
                                if alias.name == prefix or alias.name.startswith(prefix + "."):
                                    rel = py_file.relative_to(repo_root).as_posix()
                                    violations.append(f"{rel}:{node.lineno}: import {alias.name}")

                    elif isinstance(node, ast.ImportFrom):
                        module = node.module or ""
                        for prefix in self.FORBIDDEN_PREFIXES:
                            if module == prefix or module.startswith(prefix + "."):
                                rel = py_file.relative_to(repo_root).as_posix()
                                violations.append(f"{rel}:{node.lineno}: from {module} import ...")

        assert len(violations) == 0, f"Found {len(violations)} private dependency violations in generic core:\n" + "\n".join(violations)

    def test_02_generic_core_initialization_without_identifyshell(self):
        """
        Verifies generic ProviderRegistry initializes with default local providers
        and zero private IdentifyShell adapters.
        """
        ProviderRegistry.reset_instance()
        reg = ProviderRegistry.get_instance()

        assert reg.get_backend("local_process_backend") is not None
        assert reg.get_artifact_store("local_artifact_store") is not None
        assert reg.get_dataset_store("standard_dataset_store") is not None

        # Verify no IdentifyShell providers or adapters are present
        assert "extract_dinov3_embeddings" not in reg.list_adapters()
        assert reg.get_adapter("extract_dinov3_embeddings") is None

    def test_03_generic_test_suite_independence(self):
        """
        Verifies that generic tests do not directly import IdentifyShell modules.
        Private tests (test_identifyshell_integration, test_r01_dinov3_vertical_slice) are exempt.
        """
        repo_root = Path(__file__).resolve().parent.parent
        tests_root = repo_root / "tests"

        exempt_files = {
            "test_identifyshell_integration.py",
            "test_r01_dinov3_vertical_slice.py",
        }

        violations = []
        for py_file in tests_root.glob("test_*.py"):
            if py_file.name in exempt_files:
                continue

            content = py_file.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(py_file))

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        for prefix in self.FORBIDDEN_PREFIXES:
                            if alias.name == prefix or alias.name.startswith(prefix + "."):
                                violations.append(f"{py_file.name}:{node.lineno}: import {alias.name}")

                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for prefix in self.FORBIDDEN_PREFIXES:
                        if module == prefix or module.startswith(prefix + "."):
                            violations.append(f"{py_file.name}:{node.lineno}: from {module} import ...")

        assert len(violations) == 0, f"Found IdentifyShell imports in generic tests:\n" + "\n".join(violations)
