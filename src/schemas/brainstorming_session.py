from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SessionCandidate(BaseModel):
    candidate_id: str = Field(description="Stable server-generated ID e.g. cand_q_1, cand_h_1")
    type: Literal["question", "hypothesis"]
    text: str = Field(min_length=1)
    status: Literal["proposed", "accepted", "edited_and_accepted", "rejected"] = "proposed"
    source_turn_sequence: int = Field(ge=1)
    edited_text: str | None = None
    promoted_entity_id: int | None = None


class ChatMessage(BaseModel):
    role: str = Field(min_length=1, max_length=64, description="Sender role e.g. user, assistant")
    content: str = Field(min_length=1, description="Message text content")
    timestamp: str | None = Field(default=None, description="ISO timestamp of message")
    sequence: int | None = Field(default=None, description="Monotonic sequence number")
    candidates: list[dict[str, Any]] | None = Field(default_factory=list, description="Candidate items in turn")
    metadata: dict[str, Any] | None = Field(default=None, description="Optional message metadata")
    model_provenance: dict[str, Any] | None = Field(default=None, description="LLM provenance for assistant turn")


class ModelProvenance(BaseModel):
    provider: str = Field(min_length=1, max_length=128)
    model: str = Field(min_length=1, max_length=128)
    invocation_id: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: int | None = None
    prompt_sha256: str | None = None
    response_sha256: str | None = None
    extra: dict[str, Any] | None = None


class BrainstormingSessionCreate(BaseModel):
    project_id: int = Field(ge=1)
    initial_idea: str = Field(min_length=1)
    messages: list[ChatMessage] = Field(default_factory=list)
    model_provenance: dict[str, Any] | ModelProvenance | None = None
    status: str = Field(default="active", max_length=32)


class BrainstormingSessionUpdate(BaseModel):
    initial_idea: str | None = None
    messages: list[ChatMessage] | None = None
    model_provenance: dict[str, Any] | ModelProvenance | None = None
    status: str | None = Field(default=None, max_length=32)
    research_plan: dict[str, Any] | None = None


class BrainstormingSessionAddMessage(BaseModel):
    content: str = Field(min_length=1, description="User message content")
    role: Literal["user"] = Field(default="user", description="Only user role allowed from client")
    timestamp: str | None = None
    metadata: dict[str, Any] | None = None




class CandidateActionRequest(BaseModel):
    action: Literal["accept", "edit_and_accept", "reject"]
    edited_text: str | None = None
    target_question_id: int | None = None


class CandidateActionResponse(BaseModel):
    candidate: SessionCandidate
    promoted_question_id: int | None = None
    promoted_hypothesis_id: int | None = None
    message: str


class BrainstormingSessionResponse(BaseModel):
    id: int
    project_id: int
    initial_idea: str
    messages: list[dict[str, Any]]
    candidates: list[SessionCandidate] = Field(default_factory=list)
    model_provenance: dict[str, Any] | None
    status: str
    research_plan: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
