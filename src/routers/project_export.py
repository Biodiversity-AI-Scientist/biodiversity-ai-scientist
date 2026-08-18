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
    BrainstormingMessage,
    InvestigationGraph,
    InvestigationStep,
    ResearchPlan,
    Experiment,
    ExperimentRun,
    AnalysisPlan,
    AnalysisRun,
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

    questions = db.scalars(select(ResearchQuestion).where(ResearchQuestion.research_project_id == project_id)).all()
    sessions = db.scalars(select(BrainstormingSession).where(BrainstormingSession.research_project_id == project_id)).all()
    plans = db.scalars(select(ResearchPlan).where(ResearchPlan.research_project_id == project_id)).all()

    # Collect questions & hypotheses
    questions_data = []
    for q in questions:
        hypotheses = db.scalars(select(Hypothesis).where(Hypothesis.research_question_id == q.id)).all()
        graphs = db.scalars(select(InvestigationGraph).where(InvestigationGraph.research_question_id == q.id)).all()

        graphs_data = []
        for g in graphs:
            steps = db.scalars(select(InvestigationStep).where(InvestigationStep.investigation_graph_id == g.id)).all()
            graphs_data.append({
                "id": g.id,
                "title": g.title,
                "status": g.status,
                "steps": [
                    {
                        "step_number": s.step_number,
                        "title": s.title,
                        "description": s.description,
                        "status": s.status,
                    }
                    for s in steps
                ]
            })

        questions_data.append({
            "id": q.id,
            "question_text": q.question_text,
            "status": q.status,
            "hypotheses": [
                {
                    "id": h.id,
                    "statement": h.statement,
                    "status": h.status,
                }
                for h in hypotheses
            ],
            "investigation_graphs": graphs_data,
        })

    # Collect brainstorming sessions
    sessions_data = []
    for s in sessions:
        msgs = db.scalars(select(BrainstormingMessage).where(BrainstormingMessage.brainstorming_session_id == s.id)).all()
        sessions_data.append({
            "id": s.id,
            "title": s.title,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                }
                for m in msgs
            ]
        })

    return {
        "bais_format_version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "project": {
            "id": project.id,
            "title": project.title,
            "objective": project.objective,
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
