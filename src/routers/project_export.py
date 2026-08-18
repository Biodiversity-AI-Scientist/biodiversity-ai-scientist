from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.database import get_db
from src.models import (
    ResearchProject,
    ResearchQuestion,
    Hypothesis,
    BrainstormingSession,
    InvestigationStep,
    ResearchPlan,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/{project_id}/export")
def export_project_reproducibility_package(
    project_id: int,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Exports a complete scientific project as an immutable, reproducible JSON archive.
    """
    project = db.get(ResearchProject, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found.")

    questions = db.scalars(select(ResearchQuestion).where(ResearchQuestion.project_id == project_id)).all()
    sessions = db.scalars(select(BrainstormingSession).where(BrainstormingSession.project_id == project_id)).all()
    plans = db.scalars(select(ResearchPlan).where(ResearchPlan.project_id == project_id)).all()
    steps = db.scalars(select(InvestigationStep).where(InvestigationStep.project_id == project_id)).all()

    # Collect questions & hypotheses
    questions_data = []
    for q in questions:
        hypotheses = db.scalars(select(Hypothesis).where(Hypothesis.question_id == q.id)).all()
        q_steps = [s for s in steps if s.question_id == q.id]

        questions_data.append({
            "id": q.id,
            "question": q.question,
            "status": q.status,
            "source": q.source,
            "hypotheses": [
                {
                    "id": h.id,
                    "statement": h.statement,
                    "rationale": h.rationale,
                    "status": h.status,
                    "source": h.source,
                }
                for h in hypotheses
            ],
            "investigation_steps": [
                {
                    "id": s.id,
                    "step_number": s.step_number,
                    "title": s.title,
                    "description": s.description,
                    "status": s.status,
                }
                for s in q_steps
            ],
        })

    # Collect brainstorming sessions
    sessions_data = []
    for s in sessions:
        sessions_data.append({
            "id": s.id,
            "initial_idea": s.initial_idea,
            "status": s.status,
            "messages": s.messages,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })

    return {
        "bais_format_version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "project": {
            "id": project.id,
            "title": project.title,
            "objective": project.objective,
            "status": project.status,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "archived_at": project.archived_at.isoformat() if project.archived_at else None,
        },
        "research_questions": questions_data,
        "brainstorming_sessions": sessions_data,
        "research_plans": [
            {
                "id": p.id,
                "title": p.title,
                "status": p.status,
                "version": p.version,
            }
            for p in plans
        ],
    }
