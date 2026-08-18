from pydantic import BaseModel

from src.schemas.analysis_run import AnalysisRunResponse
from src.schemas.result import ResultResponse


class AnalysisExecutionResponse(BaseModel):
    run: AnalysisRunResponse
    results: list[ResultResponse]
