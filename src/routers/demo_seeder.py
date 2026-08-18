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
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/seed-demo", status_code=status.HTTP_201_CREATED)
def seed_demo_project_endpoint(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Seeds a realistic, self-contained biodiversity research project for demonstration.
    """
    # 1. Create Research Project
    project = ResearchProject(
        title="Alpine Flora Phenological Shifts & Elevational Climate Grounding",
        objective="Investigate elevation-dependent flowering phenology shifts in alpine herb communities using historical herbarium records and climate reanalysis.",
        created_at=datetime.now(timezone.utc),
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # 2. Create Research Question
    question = ResearchQuestion(
        research_project_id=project.id,
        question_text="How do earlier spring snowmelt anomalies alter flowering onset in alpine herb communities across elevation gradients (>1,800m)?",
        status="active",
        created_at=datetime.now(timezone.utc),
    )
    db.add(question)
    db.commit()
    db.refresh(question)

    # 3. Create Formal Hypothesis
    hypothesis = Hypothesis(
        research_question_id=question.id,
        statement="Earlier snowmelt advances flowering onset by 3.2 days per 1°C spring warming, with significantly greater sensitivity observed in high-elevation specialists above 2,200m.",
        status="active",
        created_at=datetime.now(timezone.utc),
    )
    db.add(hypothesis)
    db.commit()
    db.refresh(hypothesis)

    # 4. Create Brainstorming Session
    session = BrainstormingSession(
        research_project_id=project.id,
        title="Alpine Phenology Initial Exploration",
        created_at=datetime.now(timezone.utc),
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Add sample dialogue
    m1 = BrainstormingMessage(
        brainstorming_session_id=session.id,
        role="user",
        content="We want to analyze how recent alpine snowmelt changes affect flowering timing across Swiss and Austrian Alps transects.",
        timestamp=datetime.now(timezone.utc),
    )
    m2 = BrainstormingMessage(
        brainstorming_session_id=session.id,
        role="assistant",
        content="That is a compelling biogeographical inquiry. I recommend: 1. Extracting high-elevation herbarium records with georeferencing, 2. Correlating flowering dates with MODIS snow-cover duration metrics, and 3. Testing sensitivity across distinct elevational bands (Subalpine 1500-2000m vs Alpine 2000-2600m).",
        timestamp=datetime.now(timezone.utc),
    )
    db.add_all([m1, m2])
    db.commit()

    # 5. Create Investigation Graph & Steps
    graph = InvestigationGraph(
        research_question_id=question.id,
        hypothesis_id=hypothesis.id,
        title="Alpine Phenology Analysis Workflow",
        status="active",
        created_at=datetime.now(timezone.utc),
    )
    db.add(graph)
    db.commit()
    db.refresh(graph)

    step1 = InvestigationStep(
        investigation_graph_id=graph.id,
        step_number=1,
        title="Specimen Observation Extraction & Georeferencing",
        description="Filter verified GBIF occurrence records for alpine target taxa across Swiss/Austrian Alps above 1,800m.",
        status="completed",
        created_at=datetime.now(timezone.utc),
    )
    step2 = InvestigationStep(
        investigation_graph_id=graph.id,
        step_number=2,
        title="Thermal Growing Degree-Day & Snowmelt Modeling",
        description="Calculate cumulative degree-days and snow-free dates per sampling grid from ERA5-Land reanalysis.",
        status="active",
        created_at=datetime.now(timezone.utc),
    )
    step3 = InvestigationStep(
        investigation_graph_id=graph.id,
        step_number=3,
        title="Elevational Sensitivity Regression",
        description="Fit linear mixed-effects models evaluating phenological advance (days/decade) versus elevation.",
        status="pending",
        created_at=datetime.now(timezone.utc),
    )
    db.add_all([step1, step2, step3])
    db.commit()

    return {
        "success": True,
        "message": "Demo biodiversity research project seeded successfully.",
        "project_id": project.id,
        "question_id": question.id,
        "hypothesis_id": hypothesis.id,
        "session_id": session.id,
        "graph_id": graph.id,
    }
