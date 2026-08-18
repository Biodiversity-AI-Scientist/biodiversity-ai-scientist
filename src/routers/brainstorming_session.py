import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.llm.exceptions import GatewayNotConfiguredError, LLMGatewayError
from src.llm.gateway import LLMGateway
from src.models import BrainstormingSession, Hypothesis, ResearchQuestion
from src.repositories import brainstorming_session as repository
from src.repositories import research_project as project_repository
from src.schemas.brainstorming_session import (
    BrainstormingSessionAddMessage,
    BrainstormingSessionCreate,
    BrainstormingSessionResponse,
    BrainstormingSessionUpdate,
    CandidateActionRequest,
    CandidateActionResponse,
    SessionCandidate,
)
from src.services.context import build_brainstorming_context

logger = logging.getLogger(__name__)


router = APIRouter(
    tags=["Brainstorming sessions"],
)


DbSession = Annotated[
    Session,
    Depends(get_db),
]


def _generate_assistant_reply_if_needed(
    db: Session,
    session: repository.BrainstormingSession,
    dwh_db: Session | None = None,
) -> repository.BrainstormingSession:
    try:
        gateway = LLMGateway()

        dwh_session = dwh_db
        should_close_dwh = False
        override_gen = None
        if dwh_session is None:
            try:
                from src.database import get_dwh_db
                from src.main import app
                if get_dwh_db in app.dependency_overrides:
                    override_gen = app.dependency_overrides[get_dwh_db]()
                    dwh_session = next(override_gen)
            except Exception:
                dwh_session = None

        if dwh_session is None:
            try:
                from src.database import DwhSessionLocal
                dwh_session = DwhSessionLocal()
                should_close_dwh = True
            except Exception:
                dwh_session = None

        try:
            context = build_brainstorming_context(db, session.project_id, session.id, dwh_db=dwh_session)
        finally:
            if should_close_dwh and dwh_session:
                dwh_session.close()
            if override_gen:
                try:
                    override_gen.close()
                except Exception:
                    pass



        result = gateway.invoke(
            "brainstorming_turn_v1",
            inputs={
                "project_title": context.get("project_title", "Research Project"),
                "project_description": context.get("project_description", ""),
                "existing_questions": context.get("existing_questions_list", []),
                "existing_hypotheses": context.get("existing_hypotheses_list", []),
                "initial_idea": session.initial_idea,
                "conversation_history": context.get("history_turns", []),
                "data_intelligence_context": context.get("data_intelligence_context") or None,
            },
        )


        reply_text = result.output.get("reply", "")
        questions = result.output.get("suggested_questions", [])
        hypotheses = result.output.get("candidate_hypotheses", [])

        # Count existing candidates in session to generate stable sequential IDs
        existing_q_count = len([c for c in session.candidates if c.get("type") == "question"])
        existing_h_count = len([c for c in session.candidates if c.get("type") == "hypothesis"])
        next_seq = len(session.messages or []) + 1

        new_candidates = []
        for i, q in enumerate(questions):
            cand_id = f"cand_q_{existing_q_count + i + 1}"
            new_candidates.append({
                "candidate_id": cand_id,
                "type": "question",
                "text": q,
                "status": "proposed",
                "source_turn_sequence": next_seq,
                "edited_text": None,
                "promoted_entity_id": None,
            })

        for j, h in enumerate(hypotheses):
            cand_id = f"cand_h_{existing_h_count + j + 1}"
            new_candidates.append({
                "candidate_id": cand_id,
                "type": "hypothesis",
                "text": h,
                "status": "proposed",
                "source_turn_sequence": next_seq,
                "edited_text": None,
                "promoted_entity_id": None,
            })

        formatted_response = reply_text
        if questions:
            formatted_response += "\n\nSuggested Research Questions:\n" + "\n".join(
                f"- [{new_candidates[i]['candidate_id']}] {q}" for i, q in enumerate(questions)
            )
        if hypotheses:
            formatted_response += "\n\nCandidate Hypotheses:\n" + "\n".join(
                f"- [{new_candidates[len(questions) + j]['candidate_id']}] {h}" for j, h in enumerate(hypotheses)
            )

        return repository.add_assistant_message(
            db=db,
            session=session,
            content=formatted_response,
            candidates=new_candidates,
            model_provenance=result.metadata.model_dump(),
        )

    except (LLMGatewayError, GatewayNotConfiguredError) as exc:
        logger.warning("LLM response generation skipped or failed: %s", exc)

    return session


@router.post(
    "/projects/{project_id}/brainstorming-sessions",
    response_model=BrainstormingSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_brainstorming_session_for_project(
    project_id: int,
    session_data: BrainstormingSessionCreate,
    db: DbSession,
    generate_llm_response: bool = True,
):
    project = project_repository.get_project(db, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research project not found",
        )

    # Ensure session_data project_id matches path
    session_data.project_id = project_id
    session = repository.create_session(
        db=db,
        session_data=session_data,
    )

    if generate_llm_response:
        session = _generate_assistant_reply_if_needed(db, session)

    return BrainstormingSessionResponse.model_validate(session)


@router.post(
    "/brainstorming-sessions",
    response_model=BrainstormingSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_brainstorming_session(
    session_data: BrainstormingSessionCreate,
    db: DbSession,
    generate_llm_response: bool = True,
):
    project = project_repository.get_project(db, session_data.project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research project not found",
        )

    session = repository.create_session(
        db=db,
        session_data=session_data,
    )

    if generate_llm_response:
        session = _generate_assistant_reply_if_needed(db, session)

    return BrainstormingSessionResponse.model_validate(session)


@router.get(
    "/brainstorming-sessions/{session_id}",
    response_model=BrainstormingSessionResponse,
)
def get_brainstorming_session(
    session_id: int,
    db: DbSession,
):
    session = repository.get_session(db, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brainstorming session not found",
        )
    return BrainstormingSessionResponse.model_validate(session)


@router.get(
    "/projects/{project_id}/brainstorming-sessions",
    response_model=list[BrainstormingSessionResponse],
)
def list_brainstorming_sessions_for_project(
    project_id: int,
    include_archived: bool = False,
    db: DbSession = None,
):
    project = project_repository.get_project(db, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research project not found",
        )
    sessions = repository.get_sessions_by_project(db, project_id, include_archived=include_archived)
    return [BrainstormingSessionResponse.model_validate(s) for s in sessions]



@router.post(
    "/brainstorming-sessions/{session_id}/messages",
    response_model=BrainstormingSessionResponse,
)
def add_message_to_brainstorming_session(
    session_id: int,
    message_data: BrainstormingSessionAddMessage,
    db: DbSession,
    generate_llm_response: bool = True,
):
    session = repository.get_session(db, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brainstorming session not found",
        )

    # Phase 1: Persist message in MySQL
    session = repository.add_message(
        db=db,
        session=session,
        add_data=message_data,
    )

    # Phase 2: Call remote LLM gateway (if requested and message is from user) and append assistant turn
    if generate_llm_response and message_data.role == "user":
        session = _generate_assistant_reply_if_needed(db, session)

    return BrainstormingSessionResponse.model_validate(session)



@router.post(
    "/brainstorming-sessions/{session_id}/candidates/{candidate_id}/action",
    response_model=CandidateActionResponse,
)
def handle_candidate_action(
    session_id: int,
    candidate_id: str,
    action_data: CandidateActionRequest,
    db: DbSession,
) -> CandidateActionResponse:
    session = repository.get_session(db, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brainstorming session not found",
        )

    candidate = repository.get_candidate_by_id(session, candidate_id)
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate '{candidate_id}' not found in session #{session_id}",
        )

    action = action_data.action
    promoted_q_id = None
    promoted_h_id = None

    if action in ("accept", "edit_and_accept"):
        new_status = "accepted" if action == "accept" else "edited_and_accepted"
        final_text = (
            action_data.edited_text.strip()
            if action == "edit_and_accept" and action_data.edited_text
            else candidate["text"].strip()
        )

        if candidate["type"] == "question":
            # Normalized deduplication
            existing_q = (
                db.query(ResearchQuestion)
                .filter(
                    ResearchQuestion.project_id == session.project_id,
                    ResearchQuestion.question == final_text,
                )
                .first()
            )
            if existing_q:
                promoted_q_id = existing_q.id
            else:
                new_q = ResearchQuestion(
                    project_id=session.project_id,
                    question=final_text,
                    source="brainstorming",
                    brainstorming_session_id=session.id,
                    status="open",
                )
                db.add(new_q)
                db.commit()
                db.refresh(new_q)
                promoted_q_id = new_q.id

            updated_cand = repository.update_candidate_state(
                db=db,
                session=session,
                candidate_id=candidate_id,
                status=new_status,
                edited_text=final_text if action == "edit_and_accept" else None,
                promoted_entity_id=promoted_q_id,
            )
            return CandidateActionResponse(
                candidate=SessionCandidate.model_validate(updated_cand),
                promoted_question_id=promoted_q_id,
                message=f"ResearchQuestion #{promoted_q_id} promoted successfully",
            )

        elif candidate["type"] == "hypothesis":
            target_q_id = action_data.target_question_id
            if target_q_id is None:
                first_q = (
                    db.query(ResearchQuestion)
                    .filter(ResearchQuestion.project_id == session.project_id)
                    .first()
                )
                if first_q:
                    target_q_id = first_q.id
                else:
                    # Create a default parent question for this hypothesis
                    parent_q = ResearchQuestion(
                        project_id=session.project_id,
                        question=f"Research question derived from brainstorming session #{session.id}",
                        source="brainstorming",
                        brainstorming_session_id=session.id,
                        status="open",
                    )
                    db.add(parent_q)
                    db.commit()
                    db.refresh(parent_q)
                    target_q_id = parent_q.id

            # Normalized deduplication
            existing_h = (
                db.query(Hypothesis)
                .filter(
                    Hypothesis.question_id == target_q_id,
                    Hypothesis.statement == final_text,
                )
                .first()
            )
            if existing_h:
                promoted_h_id = existing_h.id
            else:
                new_h = Hypothesis(
                    question_id=target_q_id,
                    statement=final_text,
                    source="brainstorming",
                    brainstorming_session_id=session.id,
                    status="proposed",
                )
                db.add(new_h)
                db.commit()
                db.refresh(new_h)
                promoted_h_id = new_h.id

            updated_cand = repository.update_candidate_state(
                db=db,
                session=session,
                candidate_id=candidate_id,
                status=new_status,
                edited_text=final_text if action == "edit_and_accept" else None,
                promoted_entity_id=promoted_h_id,
            )
            return CandidateActionResponse(
                candidate=SessionCandidate.model_validate(updated_cand),
                promoted_hypothesis_id=promoted_h_id,
                message=f"Hypothesis #{promoted_h_id} linked to ResearchQuestion #{target_q_id} promoted successfully",
            )

    elif action == "reject":
        updated_cand = repository.update_candidate_state(
            db=db,
            session=session,
            candidate_id=candidate_id,
            status="rejected",
        )
        return CandidateActionResponse(
            candidate=SessionCandidate.model_validate(updated_cand),
            message=f"Candidate '{candidate_id}' marked as rejected",
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unknown action '{action}'",
    )


@router.patch(
    "/brainstorming-sessions/{session_id}",
    response_model=BrainstormingSessionResponse,
)
def update_brainstorming_session(
    session_id: int,
    update_data: BrainstormingSessionUpdate,
    db: DbSession,
):
    session = repository.get_session(db, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brainstorming session not found",
        )

    updated = repository.update_session(
        db=db,
        session=session,
        update_data=update_data,
    )
    return BrainstormingSessionResponse.model_validate(updated)


@router.patch(
    "/brainstorming-sessions/{session_id}/archive",
    response_model=BrainstormingSessionResponse,
)
def archive_brainstorming_session(
    session_id: int,
    db: DbSession,
):
    session = repository.get_session(db, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brainstorming session not found",
        )
    archived = repository.set_session_status(db, session, "archived")
    return BrainstormingSessionResponse.model_validate(archived)


@router.patch(
    "/brainstorming-sessions/{session_id}/unarchive",
    response_model=BrainstormingSessionResponse,
)
def unarchive_brainstorming_session(
    session_id: int,
    db: DbSession,
):
    session = repository.get_session(db, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brainstorming session not found",
        )
    active = repository.set_session_status(db, session, "active")
    return BrainstormingSessionResponse.model_validate(active)

