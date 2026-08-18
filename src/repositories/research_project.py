from datetime import datetime, timezone
import logging
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from src.models import (
    AnalysisPlan,
    AnalysisRun,
    Artifact,
    BrainstormingSession,
    CapabilityGap,
    CapabilitySelection,
    Claim,
    ClaimEdge,
    DatasetVersion,
    Decision,
    EvidenceItem,
    Hypothesis,
    InvestigationPlanGeneration,
    InvestigationStep,
    InvestigationStepDependency,
    Prediction,
    ResearchAgendaItem,
    ResearchEvent,
    ResearchPlan,
    ResearchProject,
    ResearchQuestion,
    Result,
    Review,
    SourceDocument,
)
from src.schemas.research_project import ResearchProjectCreate, ResearchProjectUpdate

logger = logging.getLogger(__name__)


def create_project(
    db: Session,
    project_data: ResearchProjectCreate,
) -> ResearchProject:
    project = ResearchProject(
        title=project_data.title,
        objective=project_data.objective,
        status="draft",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_project(
    db: Session,
    project_id: int,
) -> ResearchProject | None:
    statement = select(ResearchProject).where(
        ResearchProject.id == project_id
    )
    return db.scalar(statement)


def get_projects(
    db: Session,
    include_archived: bool = False,
) -> list[ResearchProject]:
    statement = select(ResearchProject)
    if not include_archived:
        statement = statement.where(
            ResearchProject.archived_at.is_(None),
            ResearchProject.status != "archived",
        )
    statement = statement.order_by(ResearchProject.created_at.desc())
    return list(db.scalars(statement).all())


def update_project(
    db: Session,
    project_id: int,
    data: ResearchProjectUpdate,
) -> ResearchProject | None:
    project = get_project(db, project_id)
    if not project:
        return None

    update_dict = data.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        if v is not None:
            setattr(project, k, v)

    db.commit()
    db.refresh(project)
    return project


def archive_project(
    db: Session,
    project_id: int,
) -> ResearchProject | None:
    project = get_project(db, project_id)
    if not project:
        return None

    project.status = "archived"
    project.archived_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(project)
    return project


def unarchive_project(
    db: Session,
    project_id: int,
) -> ResearchProject | None:
    project = get_project(db, project_id)
    if not project:
        return None

    project.status = "active"
    project.archived_at = None
    db.commit()
    db.refresh(project)
    return project


def delete_project(
    db: Session,
    project_id: int,
) -> bool:
    """
    Permanently deletes a ResearchProject and all associated child entities
    across all knowledge, planning, investigation, and analysis tables in a single transaction.
    """
    project = get_project(db, project_id)
    if not project:
        return False

    if project.status == "active":
        raise ValueError("Cannot delete an active research project. Please archive the project first or change its status to draft/completed.")

    try:
        # 0. Capability Selections & Gaps
        db.execute(delete(CapabilityGap).where(CapabilityGap.project_id == project_id))
        step_ids = list(
            db.scalars(
                select(InvestigationStep.id).where(InvestigationStep.project_id == project_id)
            ).all()
        )
        if step_ids:
            db.execute(delete(CapabilitySelection).where(CapabilitySelection.investigation_step_id.in_(step_ids)))
            db.execute(
                delete(InvestigationStepDependency).where(
                    (InvestigationStepDependency.step_id.in_(step_ids))
                    | (InvestigationStepDependency.depends_on_step_id.in_(step_ids))
                )
            )

        # 1. Investigation Steps & Generations
        db.execute(delete(InvestigationStep).where(InvestigationStep.project_id == project_id))
        db.execute(
            delete(InvestigationPlanGeneration).where(
                InvestigationPlanGeneration.project_id == project_id
            )
        )

        # 3. Question and Hypothesis IDs lookup
        q_ids = list(
            db.scalars(
                select(ResearchQuestion.id).where(ResearchQuestion.project_id == project_id)
            ).all()
        )
        h_ids = []
        if q_ids:
            h_ids = list(
                db.scalars(
                    select(Hypothesis.id).where(Hypothesis.question_id.in_(q_ids))
                ).all()
            )

        # 4. Analysis Plans and Runs lookup
        plan_ids = []
        if q_ids:
            plan_ids = list(
                db.scalars(
                    select(AnalysisPlan.id).where(AnalysisPlan.question_id.in_(q_ids))
                ).all()
            )
        run_ids = []
        if plan_ids:
            run_ids = list(
                db.scalars(
                    select(AnalysisRun.id).where(AnalysisRun.analysis_plan_id.in_(plan_ids))
                ).all()
            )

        # 5. Reviews linked to claims or analysis runs
        claim_ids = list(
            db.scalars(select(Claim.id).where(Claim.project_id == project_id)).all()
        )
        if claim_ids:
            db.execute(delete(Review).where(Review.claim_id.in_(claim_ids)))
        if run_ids:
            db.execute(delete(Review).where(Review.analysis_run_id.in_(run_ids)))

        # 6. Evidence, Claims, Edges
        if claim_ids:
            db.execute(
                delete(ClaimEdge).where(
                    (ClaimEdge.source_claim_id.in_(claim_ids))
                    | (ClaimEdge.target_claim_id.in_(claim_ids))
                )
            )
            db.execute(delete(EvidenceItem).where(EvidenceItem.claim_id.in_(claim_ids)))
        db.execute(delete(Claim).where(Claim.project_id == project_id))

        # 7. Decisions
        db.execute(delete(Decision).where(Decision.project_id == project_id))

        # 8. Analysis Runs, Results, Plans
        if run_ids:
            db.execute(delete(Result).where(Result.analysis_run_id.in_(run_ids)))
            db.execute(delete(AnalysisRun).where(AnalysisRun.id.in_(run_ids)))
        if plan_ids:
            db.execute(delete(AnalysisPlan).where(AnalysisPlan.id.in_(plan_ids)))

        # 9. Predictions, Hypotheses, Questions
        if h_ids:
            db.execute(delete(Prediction).where(Prediction.hypothesis_id.in_(h_ids)))
            db.execute(delete(Hypothesis).where(Hypothesis.id.in_(h_ids)))
        if q_ids:
            db.execute(delete(ResearchQuestion).where(ResearchQuestion.id.in_(q_ids)))



        # 10. Research Agenda Items & Research Plans
        db.execute(
            delete(ResearchAgendaItem).where(
                ResearchAgendaItem.origin_project_id == project_id
            )
        )
        db.execute(delete(ResearchPlan).where(ResearchPlan.project_id == project_id))


        # 8. Brainstorming Sessions
        db.execute(delete(BrainstormingSession).where(BrainstormingSession.project_id == project_id))

        # 9. Artifacts, Source Documents, Dataset Versions, Events
        db.execute(delete(Artifact).where(Artifact.project_id == project_id))
        db.execute(delete(SourceDocument).where(SourceDocument.project_id == project_id))
        db.execute(delete(DatasetVersion).where(DatasetVersion.project_id == project_id))
        db.execute(delete(ResearchEvent).where(ResearchEvent.project_id == project_id))

        # 10. Research Project
        db.execute(delete(ResearchProject).where(ResearchProject.id == project_id))

        db.commit()
        return True

    except Exception as e:
        db.rollback()
        logger.exception("Failed to delete project %s: %s", project_id, e)
        raise ValueError(f"Failed to delete project #{project_id}: {e}")
