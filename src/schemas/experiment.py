from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from src.schemas.result import ResultResponse


# ==========================================
# Canonical Experiment Schemas (Formerly AnalysisPlan)
# ==========================================

class ExperimentBase(BaseModel):
    hypothesis_id: int | None = Field(default=None, ge=1)
    dataset_version_id: int | None = Field(default=None, ge=1)
    estimand: str | None = None
    method: str = Field(min_length=1, max_length=255)
    assumptions: dict[str, Any] | None = None
    parameters: dict[str, Any] | None = None
    exploratory: bool = False


class ExperimentCreate(ExperimentBase):
    pass


class ExperimentUpdate(BaseModel):
    estimand: str | None = None
    method: str | None = None
    assumptions: dict[str, Any] | None = None
    parameters: dict[str, Any] | None = None
    status: str | None = None


class ExperimentResponse(BaseModel):
    id: int
    question_id: int
    hypothesis_id: int | None
    dataset_version_id: int | None
    estimand: str | None
    method: str
    assumptions: dict[str, Any] | None
    parameters: dict[str, Any] | None
    exploratory: bool
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExperimentPlanAIRequest(BaseModel):
    user_guidance: str | None = None


class ExperimentParameterOverrideRequest(BaseModel):
    parameters: dict[str, Any]
    justification: str | None = None


# ==========================================
# Canonical Experiment Run Schemas (Formerly AnalysisRun)
# ==========================================

class ExperimentRunCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_version_id: int | None = Field(default=None, ge=1)
    tool_name: str | None = Field(default=None, max_length=255)
    tool_version: str | None = Field(default=None, max_length=100)
    source_code_commit: str | None = Field(default=None, max_length=64)
    generated_code_hash: str | None = Field(default=None, min_length=64, max_length=64)
    container_image_digest: str | None = Field(default=None, max_length=255)
    model_version: str | None = Field(default=None, max_length=255)
    parameters: dict[str, Any] | None = None
    random_seeds: list[Any] | None = None
    hardware_metadata: dict[str, Any] | None = None
    execution_metadata: dict[str, Any] | None = None


class ExperimentRunUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_code_commit: str | None = Field(default=None, max_length=64)
    generated_code_hash: str | None = Field(default=None, min_length=64, max_length=64)
    container_image_digest: str | None = Field(default=None, max_length=255)
    model_version: str | None = Field(default=None, max_length=255)
    parameters: dict[str, Any] | None = None
    random_seeds: list[Any] | None = None
    hardware_metadata: dict[str, Any] | None = None
    execution_metadata: dict[str, Any] | None = None


class ExperimentRunStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    parameters: dict[str, Any] | None = None
    execution_metadata: dict[str, Any] | None = None
    hardware_metadata: dict[str, Any] | None = None


class ExperimentRunCompleteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    execution_metadata: dict[str, Any] | None = None


class ExperimentRunFailureRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str | None = None
    error_message: str | None = None
    error_type: str | None = None
    error_details: dict[str, Any] | list[Any] | str | None = None


class ExperimentRunResponse(BaseModel):
    id: int
    analysis_plan_id: int = Field(description="Internal ID of the parent Experiment")
    dataset_version_id: int | None = None
    status: str

    tool_name: str | None = None
    tool_version: str | None = None
    source_code_commit: str | None = None
    generated_code_hash: str | None = None
    container_image_digest: str | None = None
    model_version: str | None = None

    parameters: dict[str, Any] | None = None
    random_seeds: list[Any] | None = None
    hardware_metadata: dict[str, Any] | None = None
    execution_metadata: dict[str, Any] | None = None

    error_type: str | None = None
    error_message: str | None = None
    error_details: dict[str, Any] | list[Any] | str | None = None

    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ExperimentExecutionResponse(BaseModel):
    run: ExperimentRunResponse
    results: list[ResultResponse]


# ==========================================
# Legacy Aliases (Maintained for Backward Compatibility)
# ==========================================
AnalysisPlanBase = ExperimentBase
AnalysisPlanCreate = ExperimentCreate
AnalysisPlanUpdate = ExperimentUpdate
AnalysisPlanResponse = ExperimentResponse

AnalysisRunCreate = ExperimentRunCreate
AnalysisRunUpdate = ExperimentRunUpdate
AnalysisRunStartRequest = ExperimentRunStartRequest
AnalysisRunCompleteRequest = ExperimentRunCompleteRequest
AnalysisRunFailureRequest = ExperimentRunFailureRequest
AnalysisRunResponse = ExperimentRunResponse
