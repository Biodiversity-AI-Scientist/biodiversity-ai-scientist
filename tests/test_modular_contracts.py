"""
Unit tests for Refactoring Track R01 Generic Contracts and Providers.

Verifies that the generic core contracts, local providers, and ProviderRegistry
function independently without requiring any private IdentifyShell integrations.
"""
import os
import tempfile
from pathlib import Path
import pytest

from src.core.contracts.artifact_store import ArtifactStore, StoredArtifactInfo
from src.core.contracts.capability_adapter import (
    CapabilityAdapter,
    CapabilityExecutionOutcome,
    PreparedJob,
)
from src.core.contracts.dataset_store import DatasetStore
from src.core.contracts.execution import (
    ExecutionBackend,
    JobHandle,
    JobResources,
    JobState,
)
from src.core.providers.local_artifact_store import LocalArtifactStore
from src.core.providers.local_execution import LocalProcessExecutionBackend
from src.core.providers.registry import ProviderRegistry
from src.core.providers.standard_dataset_store import StandardDatasetStore


class FakeGenericCapabilityAdapter(CapabilityAdapter):
    """Generic test double adapter for verifying registry without private integrations."""
    @property
    def capability_key(self) -> str:
        return "fake_generic_capability"

    def validate_parameters(self, parameters: dict) -> tuple[bool, list[str]]:
        return True, []

    def prepare_execution(
        self,
        experiment_id: int,
        run_id: int,
        parameters: dict,
        dataset_version_id: int | None,
        dataset_store: DatasetStore,
        artifact_store: ArtifactStore,
    ) -> PreparedJob:
        return PreparedJob(
            command=["python3", "-c", "print('fake output')"],
            working_dir="/tmp",
            env={},
            resources=JobResources(),
            job_metadata={"test": True},
        )

    def parse_execution_output(
        self,
        experiment_id: int,
        run_id: int,
        job_handle: JobHandle,
        backend: ExecutionBackend,
        artifact_store: ArtifactStore,
    ) -> CapabilityExecutionOutcome:
        return CapabilityExecutionOutcome(
            success=True,
            summary="Fake capability execution completed",
            result_type="fake_result",
        )


class TestModularContracts:
    def setup_method(self):
        ProviderRegistry.reset_instance()

    def test_01_local_execution_backend(self):
        backend = LocalProcessExecutionBackend()
        assert backend.backend_name == "local_process_backend"

        # Dispatch a successful command
        handle = backend.dispatch_job(
            command=["python3", "-c", "print('R01 Modular Execution Success')"],
            resources=JobResources(timeout_seconds=10),
        )
        assert handle.job_id.startswith("local_job_")

        status = backend.get_job_status(handle)
        assert status.state == JobState.COMPLETED
        assert status.exit_code == 0

        logs = backend.get_execution_logs(handle)
        assert "R01 Modular Execution Success" in logs.stdout

    def test_02_local_artifact_store_integrity(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = LocalArtifactStore(base_dir=tmpdir)
            assert store.store_name == "local_artifact_store"

            # Store bytes
            data = b"Molluscan shell specimen feature vector matrix bytes"
            stored_info = store.store_bytes(
                data=data,
                artifact_type="embeddings",
                project_id=42,
                filename="features.bin",
                metadata={"dimensions": 384},
            )

            assert stored_info.size_bytes == len(data)
            assert stored_info.sha256 == ArtifactStore.compute_sha256(data)
            assert stored_info.artifact_type == "embeddings"

            # Verify checksum
            assert store.verify_checksum(stored_info.uri, stored_info.sha256) is True
            assert store.verify_checksum(stored_info.uri, "incorrect_sha256") is False

            # Retrieve path and read bytes
            path = store.retrieve_path(stored_info.uri)
            assert path.exists()
            assert store.read_bytes(stored_info.uri) == data

    def test_03_generic_provider_registry_defaults_and_fallback(self):
        registry = ProviderRegistry.get_instance()
        assert registry.get_backend("local_process_backend") is not None
        assert registry.get_artifact_store("local_artifact_store") is not None
        assert registry.get_dataset_store("standard_dataset_store") is not None

        # Fallback when unknown provider requested
        assert registry.get_backend("non_existent_gpu_host").backend_name == "local_process_backend"
        assert registry.get_artifact_store("non_existent_store").store_name == "local_artifact_store"
        assert registry.get_dataset_store("non_existent_dataset").store_name == "standard_dataset_store"

        # Initially zero private adapters in pure generic core
        assert len(registry.list_adapters()) == 0

    def test_04_generic_provider_registry_dynamic_registration(self):
        registry = ProviderRegistry.get_instance()
        fake_adapter = FakeGenericCapabilityAdapter()
        registry.register_adapter(fake_adapter)

        assert "fake_generic_capability" in registry.list_adapters()
        assert registry.get_adapter("fake_generic_capability") is fake_adapter
