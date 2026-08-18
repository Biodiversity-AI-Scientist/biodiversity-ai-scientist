"""
Provider and Adapter Registry for BAIS Core.

Manages active ExecutionBackends, ArtifactStores, DatasetStores, and CapabilityAdapters.
Provides clean dependency injection and fallback handling.
"""
from typing import Any

from src.core.contracts.artifact_store import ArtifactStore
from src.core.contracts.capability_adapter import CapabilityAdapter
from src.core.contracts.dataset_store import DatasetStore
from src.core.contracts.execution import ExecutionBackend
from src.core.providers.local_artifact_store import LocalArtifactStore
from src.core.providers.local_execution import LocalProcessExecutionBackend
from src.core.providers.standard_dataset_store import StandardDatasetStore


class ProviderRegistry:
    _instance = None

    def __init__(self):
        self._backends: dict[str, ExecutionBackend] = {}
        self._artifact_stores: dict[str, ArtifactStore] = {}
        self._dataset_stores: dict[str, DatasetStore] = {}
        self._adapters: dict[str, CapabilityAdapter] = {}

        # Default standard generic providers
        self.register_backend(LocalProcessExecutionBackend(), is_default=True)
        self.register_artifact_store(LocalArtifactStore(), is_default=True)
        self.register_dataset_store(StandardDatasetStore(), is_default=True)

        self._default_backend_name = "local_process_backend"
        self._default_artifact_store_name = "local_artifact_store"
        self._default_dataset_store_name = "standard_dataset_store"

    @classmethod
    def get_instance(cls) -> "ProviderRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (useful for clean test isolation)."""
        cls._instance = None

    # Backends
    def register_backend(self, backend: ExecutionBackend, is_default: bool = False) -> None:
        self._backends[backend.backend_name] = backend
        if is_default:
            self._default_backend_name = backend.backend_name

    def get_backend(self, name: str | None = None) -> ExecutionBackend:
        target = name or self._default_backend_name
        backend = self._backends.get(target)
        if not backend:
            # Graceful fallback to default local backend
            return self._backends[self._default_backend_name]
        return backend

    # Artifact Stores
    def register_artifact_store(self, store: ArtifactStore, is_default: bool = False) -> None:
        self._artifact_stores[store.store_name] = store
        if is_default:
            self._default_artifact_store_name = store.store_name

    def get_artifact_store(self, name: str | None = None) -> ArtifactStore:
        target = name or self._default_artifact_store_name
        store = self._artifact_stores.get(target)
        if not store:
            return self._artifact_stores[self._default_artifact_store_name]
        return store

    # Dataset Stores
    def register_dataset_store(self, store: DatasetStore, is_default: bool = False) -> None:
        self._dataset_stores[store.store_name] = store
        if is_default:
            self._default_dataset_store_name = store.store_name

    def get_dataset_store(self, name: str | None = None) -> DatasetStore:
        target = name or self._default_dataset_store_name
        store = self._dataset_stores.get(target)
        if not store:
            return self._dataset_stores[self._default_dataset_store_name]
        return store

    # Capability Adapters
    def register_adapter(self, adapter: CapabilityAdapter) -> None:
        self._adapters[adapter.capability_key] = adapter

    def get_adapter(self, capability_key: str) -> CapabilityAdapter | None:
        return self._adapters.get(capability_key)

    def list_adapters(self) -> list[str]:
        return list(self._adapters.keys())
