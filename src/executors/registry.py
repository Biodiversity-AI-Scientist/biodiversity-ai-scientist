from src.executors.base import AnalysisExecutor
from src.executors.dataset_registration_summary import (
    DatasetRegistrationSummaryExecutor,
)
from src.executors.generic_executor import GenericScientificExecutor


class UnknownAnalysisTypeError(LookupError):
    pass


EXECUTORS: dict[str, AnalysisExecutor] = {
    DatasetRegistrationSummaryExecutor.analysis_type: (
        DatasetRegistrationSummaryExecutor()
    ),
    "Workflow integrity validation": (
        DatasetRegistrationSummaryExecutor()
    ),
}


def get_executor(analysis_type: str) -> AnalysisExecutor:
    executor = EXECUTORS.get(analysis_type)
    if executor is None:
        raise UnknownAnalysisTypeError(
            f"No registered executor for analysis type '{analysis_type}'"
        )
    return executor


