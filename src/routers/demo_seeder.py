from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import (
    ResearchProject,
    ResearchQuestion,
    Hypothesis,
    BrainstormingSession,
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
        status="active",
        created_at=datetime.now(timezone.utc),
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # 2. Create Brainstorming Session
    session = BrainstormingSession(
        project_id=project.id,
        initial_idea="How are alpine plant phenology dates advancing across Swiss and Austrian Alps elevations?",
        status="active",
        messages=[
            {
                "role": "user",
                "content": "We want to analyze how recent alpine snowmelt changes affect flowering timing across elevation transects.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            {
                "role": "assistant",
                "content": "I recommend formulating a hypothesis comparing high-elevation specialists above 2,200m against lower subalpine species using GBIF occurrences and ERA5 thermal metrics.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ],
        created_at=datetime.now(timezone.utc),
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # 3. Create Research Question
    question = ResearchQuestion(
        project_id=project.id,
        question="How do earlier spring snowmelt anomalies alter flowering onset in alpine herb communities across elevation gradients (>1,800m)?",
        status="open",
        source="brainstorming",
        brainstorming_session_id=session.id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(question)
    db.commit()
    db.refresh(question)

    # 4. Create Formal Hypothesis
    hypothesis = Hypothesis(
        question_id=question.id,
        statement="Earlier snowmelt advances flowering onset by 3.2 days per 1°C spring warming, with significantly greater sensitivity observed in high-elevation specialists above 2,200m.",
        rationale="High-elevation taxa rely on thermal cues directly following snow-cover disappearance.",
        status="proposed",
        source="brainstorming",
        brainstorming_session_id=session.id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(hypothesis)
    db.commit()
    db.refresh(hypothesis)

    # 5. Create Investigation Steps
    step1 = InvestigationStep(
        project_id=project.id,
        question_id=question.id,
        title="Specimen Observation Extraction & Georeferencing",
        scientific_goal="Filter verified GBIF occurrence records for alpine target taxa across Swiss/Austrian Alps above 1,800m.",
        rationale="Establish empirical baseline occurrences across elevation gradients.",
        step_type="observation",
        status="completed",
        requires_capability=True,
        requires_experiment=False,
        created_at=datetime.now(timezone.utc),
    )
    step2 = InvestigationStep(
        project_id=project.id,
        question_id=question.id,
        title="Thermal Growing Degree-Day & Snowmelt Modeling",
        scientific_goal="Calculate cumulative degree-days and snow-free dates per sampling grid from ERA5-Land reanalysis.",
        rationale="Quantify thermal forcing mechanisms driving phenological onset.",
        step_type="modeling",
        status="active",
        requires_capability=True,
        requires_experiment=True,
        created_at=datetime.now(timezone.utc),
    )
    step3 = InvestigationStep(
        project_id=project.id,
        question_id=question.id,
        title="Elevational Sensitivity Regression",
        scientific_goal="Fit linear mixed-effects models evaluating phenological advance (days/decade) versus elevation.",
        rationale="Statistically test whether higher elevation populations demonstrate accelerated sensitivity.",
        step_type="analysis",
        status="draft",
        requires_capability=False,
        requires_experiment=False,
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
    }
