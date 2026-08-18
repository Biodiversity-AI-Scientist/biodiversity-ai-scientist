"""
Generic Core Contract: CapabilityAdapter

Defines abstract interface for wrapping scientific applications, data prep,
command preparation, and output/artifact extraction.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from pydantic import BaseModel

from src.core.contracts.artifact_store import ArtifactStore, StoredArtifactInfo
from src.core.contracts.dataset_store import DatasetStore
from src.core.contracts.execution import ExecutionBackend, JobHandle, JobResources


@dataclass(frozen=True)
class PreparedJob:
    command: list[str]
    working_dir: str | None
    env: dict[str, str] = field(default_factory=dict)
    resources: JobResources = field(default_factory=JobResources)
    job_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CapabilityExecutionOutcome:
    success: bool
    summary: str
    result_type: str
    metrics: dict[str, Any] = field(default_factory=dict)
    artifacts: list[StoredArtifactInfo] = field(default_factory=list)
    diagnostics: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None


class CapabilityAdapter(ABC):
    @property
    @abstractmethod
    def capability_key(self) -> str:
        """Unique key identifying the capability this adapter handles."""
        ...

    @abstractmethod
    def validate_parameters(self, parameters: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validates parameter payload against expected adapter constraints."""
        ...

    @abstractmethod
    def prepare_execution(
        self,
        experiment_id: int,
        run_id: int,
        parameters: dict[str, Any],
        dataset_version_id: int | None,
        dataset_store: DatasetStore,
        artifact_store: ArtifactStore,
    ) -> PreparedJob:
        """Prepares commands, arguments, input manifests, and environment for execution."""
        ...

    @abstractmethod
    def parse_execution_output(
        self,
        experiment_id: int,
        run_id: int,
        job_handle: JobHandle,
        backend: ExecutionBackend,
        artifact_store: ArtifactStore,
    ) -> CapabilityExecutionOutcome:
        """Parses output files, logs, and artifacts from completed execution."""
        ...
