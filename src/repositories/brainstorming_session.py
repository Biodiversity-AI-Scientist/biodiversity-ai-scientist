from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import BrainstormingSession, ResearchProject
from src.schemas.brainstorming_session import (
    BrainstormingSessionAddMessage,
    BrainstormingSessionCreate,
    BrainstormingSessionUpdate,
    SessionCandidate,
)


def create_session(
    db: Session,
    session_data: BrainstormingSessionCreate,
) -> BrainstormingSession:
    messages_list = []
    for idx, msg in enumerate(session_data.messages):
        msg_dict = msg.model_dump() if hasattr(msg, "model_dump") else dict(msg)
        if "sequence" not in msg_dict or msg_dict["sequence"] is None:
            msg_dict["sequence"] = idx + 1
        if "timestamp" not in msg_dict or not msg_dict["timestamp"]:
            msg_dict["timestamp"] = datetime.now(timezone.utc).isoformat()
        messages_list.append(msg_dict)

    model_prov = (
        session_data.model_provenance.model_dump()
        if hasattr(session_data.model_provenance, "model_dump")
        else session_data.model_provenance
    )

    session = BrainstormingSession(
        project_id=session_data.project_id,
        initial_idea=session_data.initial_idea,
        messages=messages_list,
        model_provenance=model_prov,
        status=session_data.status,
    )

    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(
    db: Session,
    session_id: int,
) -> BrainstormingSession | None:
    statement = select(BrainstormingSession).where(
        BrainstormingSession.id == session_id
    )
    return db.scalar(statement)


def get_sessions_by_project(
    db: Session,
    project_id: int,
    include_archived: bool = False,
) -> list[BrainstormingSession]:
    query = select(BrainstormingSession).where(BrainstormingSession.project_id == project_id)
    if not include_archived:
        query = query.where(BrainstormingSession.status != "archived")
    statement = query.order_by(BrainstormingSession.created_at.desc())
    return list(db.scalars(statement).all())


def set_session_status(
    db: Session,
    session: BrainstormingSession,
    status: str,
) -> BrainstormingSession:
    session.status = status
    db.commit()
    db.refresh(session)
    return session



def add_user_message(
    db: Session,
    session: BrainstormingSession,
    content: str,
    timestamp: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> BrainstormingSession:
    current_messages = list(session.messages or [])
    seq = len(current_messages) + 1
    new_message = {
        "role": "user",
        "content": content,
        "sequence": seq,
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
    }
    if metadata:
        new_message["metadata"] = metadata

    current_messages.append(new_message)
    session.messages = current_messages
    db.commit()
    db.refresh(session)
    return session


def add_assistant_message(
    db: Session,
    session: BrainstormingSession,
    content: str,
    candidates: list[dict[str, Any]] | None = None,
    model_provenance: dict[str, Any] | None = None,
    timestamp: str | None = None,
) -> BrainstormingSession:
    current_messages = list(session.messages or [])
    seq = len(current_messages) + 1
    new_message = {
        "role": "assistant",
        "content": content,
        "sequence": seq,
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
        "candidates": candidates or [],
        "model_provenance": model_provenance,
    }
    current_messages.append(new_message)
    session.messages = current_messages
    if model_provenance:
        session.model_provenance = model_provenance

    db.commit()
    db.refresh(session)
    return session


def add_message(
    db: Session,
    session: BrainstormingSession,
    add_data: BrainstormingSessionAddMessage,
) -> BrainstormingSession:
    current_messages = list(session.messages or [])
    seq = len(current_messages) + 1
    new_message = {
        "role": getattr(add_data, "role", "user") or "user",
        "content": add_data.content,
        "sequence": seq,
        "timestamp": add_data.timestamp or datetime.now(timezone.utc).isoformat(),
    }
    if add_data.metadata:
        new_message["metadata"] = add_data.metadata

    current_messages.append(new_message)
    session.messages = current_messages

    if hasattr(add_data, "model_provenance") and add_data.model_provenance is not None:
        prov = (
            add_data.model_provenance.model_dump()
            if hasattr(add_data.model_provenance, "model_dump")
            else add_data.model_provenance
        )
        new_message["model_provenance"] = prov
        session.model_provenance = prov

    db.commit()
    db.refresh(session)
    return session


def get_candidate_by_id(
    session: BrainstormingSession,
    candidate_id: str,
) -> dict[str, Any] | None:
    for msg in session.messages or []:
        if isinstance(msg, dict) and "candidates" in msg and isinstance(msg["candidates"], list):
            for cand in msg["candidates"]:
                if isinstance(cand, dict) and cand.get("candidate_id") == candidate_id:
                    return cand
    return None


def update_candidate_state(
    db: Session,
    session: BrainstormingSession,
    candidate_id: str,
    status: str,
    edited_text: str | None = None,
    promoted_entity_id: int | None = None,
) -> dict[str, Any] | None:
    current_messages = list(session.messages or [])
    found_candidate = None

    for msg in current_messages:
        if isinstance(msg, dict) and "candidates" in msg and isinstance(msg["candidates"], list):
            for cand in msg["candidates"]:
                if isinstance(cand, dict) and cand.get("candidate_id") == candidate_id:
                    cand["status"] = status
                    if edited_text is not None:
                        cand["edited_text"] = edited_text
                    if promoted_entity_id is not None:
                        cand["promoted_entity_id"] = promoted_entity_id
                    found_candidate = cand
                    break

    if found_candidate:
        session.messages = current_messages
        db.commit()
        db.refresh(session)
        return found_candidate

    return None


def update_session(
    db: Session,
    session: BrainstormingSession,
    update_data: BrainstormingSessionUpdate,
) -> BrainstormingSession:
    if update_data.initial_idea is not None:
        session.initial_idea = update_data.initial_idea

    if update_data.messages is not None:
        messages_list = [
            msg.model_dump() if hasattr(msg, "model_dump") else msg
            for msg in update_data.messages
        ]
        session.messages = messages_list

    if update_data.model_provenance is not None:
        prov = (
            update_data.model_provenance.model_dump()
            if hasattr(update_data.model_provenance, "model_dump")
            else update_data.model_provenance
        )
        session.model_provenance = prov

    if update_data.status is not None:
        session.status = update_data.status

    if update_data.research_plan is not None:
        session.research_plan = update_data.research_plan

    db.commit()
    db.refresh(session)
    return session
