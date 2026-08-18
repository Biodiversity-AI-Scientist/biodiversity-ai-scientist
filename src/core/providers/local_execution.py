"""
Local Process ExecutionBackend Implementation.

Executes jobs locally using subprocess, tracking PID, exit code, stdout/stderr,
and resource timeouts.
"""
import os
import subprocess
import threading
import time
from datetime import datetime, timezone
from typing import Any

from src.core.contracts.execution import (
    ExecutionBackend,
    ExecutionLogs,
    JobHandle,
    JobResources,
    JobState,
    JobStatus,
)


class LocalProcessExecutionBackend(ExecutionBackend):
    def __init__(self, name: str = "local_process_backend"):
        self._name = name
        self._jobs: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    @property
    def backend_name(self) -> str:
        return self._name

    def dispatch_job(
        self,
        command: list[str],
        working_dir: str | None = None,
        env: dict[str, str] | None = None,
        resources: JobResources | None = None,
        job_metadata: dict[str, Any] | None = None,
    ) -> JobHandle:
        job_id = f"local_job_{int(time.time() * 1000)}_{os.getpid()}_{len(self._jobs) + 1}"
        res = resources or JobResources()
        merged_env = {**os.environ, **(env or {})}

        handle = JobHandle(
            job_id=job_id,
            backend_name=self.backend_name,
            submitted_at=datetime.now(timezone.utc),
            metadata=job_metadata or {},
        )

        with self._lock:
            self._jobs[job_id] = {
                "handle": handle,
                "command": command,
                "working_dir": working_dir,
                "state": JobState.PENDING,
                "started_at": None,
                "completed_at": None,
                "exit_code": None,
                "stdout": "",
                "stderr": "",
                "error_message": None,
                "process": None,
            }

        # Run process synchronously or in worker thread
        def _run():
            with self._lock:
                self._jobs[job_id]["state"] = JobState.RUNNING
                self._jobs[job_id]["started_at"] = datetime.now(timezone.utc)

            try:
                proc = subprocess.Popen(
                    command,
                    cwd=working_dir,
                    env=merged_env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                with self._lock:
                    self._jobs[job_id]["process"] = proc

                stdout_data, stderr_data = proc.communicate(timeout=res.timeout_seconds)
                exit_code = proc.returncode

                with self._lock:
                    self._jobs[job_id]["stdout"] = stdout_data or ""
                    self._jobs[job_id]["stderr"] = stderr_data or ""
                    self._jobs[job_id]["exit_code"] = exit_code
                    self._jobs[job_id]["completed_at"] = datetime.now(timezone.utc)
                    self._jobs[job_id]["state"] = (
                        JobState.COMPLETED if exit_code == 0 else JobState.FAILED
                    )
                    if exit_code != 0:
                        self._jobs[job_id]["error_message"] = (
                            f"Process exited with non-zero code {exit_code}: {stderr_data[:500]}"
                        )

            except subprocess.TimeoutExpired:
                with self._lock:
                    if self._jobs[job_id]["process"]:
                        self._jobs[job_id]["process"].kill()
                    self._jobs[job_id]["state"] = JobState.FAILED
                    self._jobs[job_id]["error_message"] = f"Job timed out after {res.timeout_seconds}s"
                    self._jobs[job_id]["completed_at"] = datetime.now(timezone.utc)
            except Exception as e:
                with self._lock:
                    self._jobs[job_id]["state"] = JobState.FAILED
                    self._jobs[job_id]["error_message"] = str(e)
                    self._jobs[job_id]["completed_at"] = datetime.now(timezone.utc)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        thread.join()  # Wait for synchronous local completion

        return handle

    def get_job_status(self, handle: JobHandle) -> JobStatus:
        with self._lock:
            info = self._jobs.get(handle.job_id)
            if not info:
                return JobStatus(job_id=handle.job_id, state=JobState.FAILED, error_message="Job not found")
            return JobStatus(
                job_id=handle.job_id,
                state=info["state"],
                exit_code=info["exit_code"],
                started_at=info["started_at"],
                completed_at=info["completed_at"],
                error_message=info["error_message"],
            )

    def get_execution_logs(self, handle: JobHandle) -> ExecutionLogs:
        with self._lock:
            info = self._jobs.get(handle.job_id, {})
            stdout = info.get("stdout", "")
            stderr = info.get("stderr", "")
            tail = [line for line in stdout.splitlines()[-20:] if line.strip()]
            return ExecutionLogs(stdout=stdout, stderr=stderr, tail_lines=tail)

    def cancel_job(self, handle: JobHandle) -> bool:
        with self._lock:
            info = self._jobs.get(handle.job_id)
            if not info:
                return False
            proc = info.get("process")
            if proc and info["state"] == JobState.RUNNING:
                proc.terminate()
                info["state"] = JobState.CANCELLED
                return True
            return False
