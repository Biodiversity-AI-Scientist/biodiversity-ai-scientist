from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import ResearchPlan, ResearchProject


def get_project(db: Session, project_id: int) -> ResearchProject | None:
    return db.get(ResearchProject, project_id)


def get_plan(db: Session, plan_id: int) -> ResearchPlan | None:
    return db.get(ResearchPlan, plan_id)


def get_plans_for_project(
    db: Session,
    project_id: int,
    include_archived: bool = False,
) -> list[ResearchPlan]:
    query = select(ResearchPlan).where(ResearchPlan.project_id == project_id)
    if not include_archived:
        query = query.where(ResearchPlan.status != "archived")
    statement = query.order_by(ResearchPlan.id.desc())
    return list(db.scalars(statement).all())


def set_plan_status(
    db: Session,
    plan: ResearchPlan,
    status: str,
) -> ResearchPlan:
    plan.status = status
    db.commit()
    db.refresh(plan)
    return plan



def get_plans_for_session(db: Session, session_id: int) -> list[ResearchPlan]:
    statement = (
        select(ResearchPlan)
        .where(ResearchPlan.brainstorming_session_id == session_id)
        .order_by(ResearchPlan.version.desc())
    )
    return list(db.scalars(statement).all())


def create_plan(
    db: Session,
    project_id: int,
    session_id: int | None,
    title: str,
    content: dict[str, Any],
    version: int = 1,
    parent_plan_id: int | None = None,
    model_provenance: dict[str, Any] | None = None,
) -> ResearchPlan:
    plan = ResearchPlan(
        project_id=project_id,
        brainstorming_session_id=session_id,
        parent_plan_id=parent_plan_id,
        version=version,
        title=title,
        status="draft",
        content=content,
        model_provenance=model_provenance,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def update_plan(
    db: Session,
    plan_id: int,
    title: str | None = None,
    status: str | None = None,
    content: dict[str, Any] | None = None,
) -> ResearchPlan | None:
    plan = db.get(ResearchPlan, plan_id)
    if plan is None:
        return None

    if title is not None:
        plan.title = title
    if status is not None:
        plan.status = status
    if content is not None:
        plan.content = content

    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def revise_plan(
    db: Session,
    parent_plan: ResearchPlan,
    new_content: dict[str, Any],
    new_title: str | None = None,
    model_provenance: dict[str, Any] | None = None,
) -> ResearchPlan:
    new_version = parent_plan.version + 1
    revised_title = new_title or f"{parent_plan.title} (v{new_version})"

    new_plan = ResearchPlan(
        project_id=parent_plan.project_id,
        brainstorming_session_id=parent_plan.brainstorming_session_id,
        parent_plan_id=parent_plan.id,
        version=new_version,
        title=revised_title,
        status="draft",
        content=new_content,
        model_provenance=model_provenance,
    )
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)
    return new_plan


def approve_plan(db: Session, plan_id: int) -> ResearchPlan | None:
    plan = db.get(ResearchPlan, plan_id)
    if plan is None:
        return None

    plan.status = "approved"
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan
