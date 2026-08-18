from pydantic import BaseModel, ConfigDict

from src.executors.base import (
    AnalysisExecutionContext,
    AnalysisExecutionOutput,
    AnalysisResultOutput,
)


class DatasetRegistrationSummaryParameters(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DatasetRegistrationSummaryExecutor:
    analysis_type = "dataset_registration_summary"
    version = "1.0.0"
    parameter_schema = DatasetRegistrationSummaryParameters

    def execute(
        self,
        context: AnalysisExecutionContext,
    ) -> AnalysisExecutionOutput:
        dataset = context.dataset_version
        grouping_keys = dataset.grouping_keys or []

        payload = {
            "dataset_version_id": dataset.id,
            "version_key": dataset.version_key,
            "source_system": dataset.source_system,
            "declared_member_count": dataset.member_count,
            "grouping_key_count": len(grouping_keys),
            "grouping_keys": list(grouping_keys),
            "has_selection_definition": (
                dataset.selection_definition is not None
            ),
            "has_manifest_uri": dataset.manifest_uri is not None,
            "has_manifest_sha256": dataset.manifest_sha256 is not None,
        }

        if dataset.member_count is None:
            count_summary = "has no declared member count"
        else:
            count_summary = (
                f"declares {dataset.member_count} dataset members"
            )

        summary = (
            f"DatasetVersion {dataset.version_key} {count_summary}; "
            f"{len(grouping_keys)} grouping keys are registered. "
            "This summarizes registration metadata and does not inspect "
            "observation-level records."
        )

        return AnalysisExecutionOutput(
            results=(
                AnalysisResultOutput(
                    result_type=self.analysis_type,
                    summary=summary,
                    payload=payload,
                    diagnostics={
                        "input_scope": "dataset_version_registration_metadata",
                        "observation_manifest_inspected": False,
                    },
                ),
            ),
        )
