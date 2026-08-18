from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import BaseModel

from src.models import AnalysisPlan, AnalysisRun, DatasetVersion


class AnalysisComputationError(RuntimeError):
    """A safe, user-displayable scientific computation failure."""


@dataclass(frozen=True)
class AnalysisExecutionContext:
    analysis_run: AnalysisRun
    analysis_plan: AnalysisPlan
    dataset_version: DatasetVersion
    parameters: BaseModel


@dataclass(frozen=True)
class AnalysisResultOutput:
    result_type: str
    summary: str
    payload: dict[str, Any]
    uncertainty: dict[str, Any] | None = None
    diagnostics: dict[str, Any] | None = None


@dataclass(frozen=True)
class AnalysisExecutionOutput:
    results: tuple[AnalysisResultOutput, ...]


class AnalysisExecutor(Protocol):
    analysis_type: str
    version: str
    parameter_schema: type[BaseModel]

    def execute(
        self,
        context: AnalysisExecutionContext,
    ) -> AnalysisExecutionOutput:
        ...
