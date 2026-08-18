import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.database import get_db, get_dwh_db
from src.schemas.intelligence_packet import (
    IntelligenceLayer,
    ResearchIntelligencePacket,
)
from src.services.orchestrator import (
    classify_intelligence_needs,
    assemble_intelligence_packet,
    format_packet_for_llm_prompt,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orchestrator", tags=["adaptive_orchestration"])


class RouteDecisionRequest(BaseModel):
    query: str
    session_history_snippet: str = ""


class RouteDecisionResponse(BaseModel):
    activated_layers: list[IntelligenceLayer]
    routing_rationale: str


class InspectPacketRequest(BaseModel):
    query: str
    project_id: int | None = None


class InspectPacketResponse(BaseModel):
    packet: ResearchIntelligencePacket
    formatted_prompt: str


@router.post("/route-decision", response_model=RouteDecisionResponse)
def get_routing_decision(req: RouteDecisionRequest) -> RouteDecisionResponse:
    """
    Returns the dynamic intelligence layers selected for a given question.
    """
    activated, rationale = classify_intelligence_needs(
        query=req.query,
        session_history_snippet=req.session_history_snippet,
    )
    return RouteDecisionResponse(
        activated_layers=list(activated),
        routing_rationale=rationale,
    )


@router.post("/inspect-packet", response_model=InspectPacketResponse)
def inspect_intelligence_packet(
    req: InspectPacketRequest,
    db: Session = Depends(get_db),
    dwh_db: Session | None = Depends(get_dwh_db),
) -> InspectPacketResponse:
    """
    Assembles and returns the full ResearchIntelligencePacket and prompt formatting without invoking the LLM.
    """
    project_ctx = {"project_id": req.project_id} if req.project_id else {}
    packet = assemble_intelligence_packet(
        db=db,
        dwh_db=dwh_db,
        project_id=req.project_id,
        user_query=req.query,
        project_context=project_ctx,
    )
    formatted = format_packet_for_llm_prompt(packet)
    return InspectPacketResponse(
        packet=packet,
        formatted_prompt=formatted,
    )
