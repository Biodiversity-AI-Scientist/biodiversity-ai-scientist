"""
Generic Core Contract: ExecutionBackend

Defines abstract interface for job dispatch, lifecycle monitoring, and resource management
without assuming specific local, SSH, Slurm, or Docker infrastructure.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class JobState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class JobResources:
    gpu_count: int = 0
    gpu_model: str | None = None
    cpu_cores: int = 1
    memory_mb: int = 4096
    timeout_seconds: int = 3600


@dataclass(frozen=True)
class JobHandle:
    job_id: str
    backend_name: str
    submitted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class JobStatus:
    job_id: str
    state: JobState
    exit_code: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class ExecutionLogs:
    stdout: str
    stderr: str
    tail_lines: list[str] = field(default_factory=list)


class ExecutionBackend(ABC):
    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Unique identifier of the execution backend."""
        ...

    @abstractmethod
    def dispatch_job(
        self,
        command: list[str],
        working_dir: str | None = None,
        env: dict[str, str] | None = None,
        resources: JobResources | None = None,
        job_metadata: dict[str, Any] | None = None,
    ) -> JobHandle:
        """Dispatches an executable job to the backend."""
        ...

    @abstractmethod
    def get_job_status(self, handle: JobHandle) -> JobStatus:
        """Retrieves the current execution status of a job."""
        ...

    @abstractmethod
    def get_execution_logs(self, handle: JobHandle) -> ExecutionLogs:
        """Retrieves standard output and error logs from the execution."""
        ...

    @abstractmethod
    def cancel_job(self, handle: JobHandle) -> bool:
        """Attempts to cancel a running or pending job."""
        ...
