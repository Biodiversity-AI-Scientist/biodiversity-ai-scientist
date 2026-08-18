import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.llm.exceptions import GatewayNotConfiguredError, LLMGatewayError
from src.llm.gateway import LLMGateway
from src.models import BrainstormingSession, Hypothesis, ResearchQuestion
from src.repositories import research_plan as repository
from src.repositories import research_project as project_repository
from src.schemas.research_plan import (
    ResearchPlanCreate,
    ResearchPlanPromote,
    ResearchPlanResponse,
    ResearchPlanRevise,
    ResearchPlanUpdate,
)
from src.services.context import build_brainstorming_context

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Research plans"],
)

DbSession = Annotated[
    Session,
    Depends(get_db),
]


@router.post(
    "/brainstorming-sessions/{session_id}/research-plan",
    response_model=ResearchPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_research_plan(
    session_id: int,
    db: DbSession,
) -> ResearchPlanResponse:
    session = db.get(BrainstormingSession, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"BrainstormingSession #{session_id} not found",
        )

    dwh_session = None
    should_close_dwh = False
    override_gen = None
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



    model_provenance = None
    structured_content = None

    try:
        gateway = LLMGateway()
        existing_info = ""
        if context.get("existing_questions_list"):
            existing_info += "\nExisting Canonical Questions:\n" + "\n".join(context["existing_questions_list"])
        if context.get("existing_hypotheses_list"):
            existing_info += "\nExisting Canonical Hypotheses:\n" + "\n".join(context["existing_hypotheses_list"])

        steering = "Synthesize the scientific brainstorming discussion into a comprehensive, structured 20-field research plan."
        if existing_info:
            steering += f"\nProject Canonical State:{existing_info}"

        result = gateway.invoke(
            "research_plan_generation_v1",
            {
                "project_title": context.get("project_title", f"Project #{session.project_id}"),
                "initial_idea": context.get("initial_idea", session.initial_idea),
                "accepted_questions": context.get("existing_questions_list", []),
                "accepted_hypotheses": context.get("existing_hypotheses_list", []),
                "conversation_summary": context.get("conversation_summary", ""),
                "steering_instructions": steering,
                "data_intelligence_context": context.get("data_intelligence_context") or None,
            },
        )

        structured_content = result.output
        model_provenance = result.metadata.model_dump()

    except (GatewayNotConfiguredError, LLMGatewayError) as exc:
        logger.warning(
            "LLM Gateway plan generation unavailable or failed: %s", exc
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM Gateway plan generation failed: {exc}",
        ) from exc

    working_title = (
        structured_content.get("working_title")
        or f"Research Plan for Session #{session_id}"
    )

    plan = repository.create_plan(
        db=db,
        project_id=session.project_id,
        session_id=session.id,
        title=working_title,
        content=structured_content,
        version=1,
        model_provenance=model_provenance,
    )

    return ResearchPlanResponse.model_validate(plan)


@router.get(
    "/projects/{project_id}/research-plans",
    response_model=list[ResearchPlanResponse],
)
def list_research_plans_for_project(
    project_id: int,
    include_archived: bool = False,
    db: DbSession = None,
) -> list[ResearchPlanResponse]:
    project = project_repository.get_project(db, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ResearchProject #{project_id} not found",
        )

    plans = repository.get_plans_for_project(db, project_id, include_archived=include_archived)
    return [ResearchPlanResponse.model_validate(p) for p in plans]



@router.get(
    "/research-plans/{plan_id}",
    response_model=ResearchPlanResponse,
)
def get_research_plan(
    plan_id: int,
    db: DbSession,
) -> ResearchPlanResponse:
    plan = repository.get_plan(db, plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ResearchPlan #{plan_id} not found",
        )

    return ResearchPlanResponse.model_validate(plan)


@router.put(
    "/research-plans/{plan_id}",
    response_model=ResearchPlanResponse,
)
def update_research_plan(
    plan_id: int,
    plan_data: ResearchPlanUpdate,
    db: DbSession,
) -> ResearchPlanResponse:
    plan = repository.get_plan(db, plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ResearchPlan #{plan_id} not found",
        )

    content_dict = (
        plan_data.content.model_dump() if plan_data.content is not None else None
    )

    # Immutability enforcement: under_review and approved plans cannot have their content edited
    if plan.status in ("under_review", "approved") and content_dict is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot modify content of research plan with status '{plan.status}'. Revisions must be made via /revise to create version N+1.",
        )

    updated_plan = repository.update_plan(
        db=db,
        plan_id=plan_id,
        title=plan_data.title,
        status=plan_data.status,
        content=content_dict,
    )

    return ResearchPlanResponse.model_validate(updated_plan)


@router.post(
    "/research-plans/{plan_id}/revise",
    response_model=ResearchPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
def revise_research_plan(
    plan_id: int,
    revise_data: ResearchPlanRevise,
    db: DbSession,
) -> ResearchPlanResponse:
    parent_plan = repository.get_plan(db, plan_id)
    if parent_plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ResearchPlan #{plan_id} not found",
        )

    context = build_brainstorming_context(
        db, parent_plan.project_id, parent_plan.brainstorming_session_id
    )

    model_provenance = None
    structured_content = None

    try:
        gateway = LLMGateway()
        steering = f"Previous Plan Title (v{parent_plan.version}): {parent_plan.title}\n"
        if parent_plan.content:
            steering += f"Previous Plan Objective: {parent_plan.content.get('research_objective', '')}\n"
            steering += f"Previous Research Strategy: {parent_plan.content.get('proposed_research_strategy', '')}\n"
        steering += f"\nResearcher Steering Instructions for Revision: {revise_data.steering_instructions}"

        result = gateway.invoke(
            "research_plan_generation_v1",
            {
                "project_title": context.get("project_title", f"Project #{parent_plan.project_id}"),
                "initial_idea": context.get("initial_idea", parent_plan.title),
                "accepted_questions": context.get("existing_questions_list", []),
                "accepted_hypotheses": context.get("existing_hypotheses_list", []),
                "conversation_summary": context.get("conversation_summary", ""),
                "steering_instructions": steering,
                "data_intelligence_context": context.get("data_intelligence_context") or None,
            },
        )
        structured_content = result.output
        model_provenance = result.metadata.model_dump()
    except (GatewayNotConfiguredError, LLMGatewayError) as exc:
        logger.warning("LLM Gateway plan revision failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM Gateway plan revision failed: {exc}",
        ) from exc


    working_title = (
        structured_content.get("working_title")
        or f"{parent_plan.title} (v{parent_plan.version + 1})"
    )

    new_plan = repository.revise_plan(
        db=db,
        parent_plan=parent_plan,
        new_content=structured_content,
        new_title=working_title,
        model_provenance=model_provenance,
    )

    return ResearchPlanResponse.model_validate(new_plan)


@router.post(
    "/research-plans/{plan_id}/approve",
    response_model=ResearchPlanResponse,
)
def approve_research_plan(
    plan_id: int,
    db: DbSession,
) -> ResearchPlanResponse:
    plan = repository.get_plan(db, plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ResearchPlan #{plan_id} not found",
        )

    if plan.status == "approved":
        return ResearchPlanResponse.model_validate(plan)

    approved = repository.approve_plan(db, plan_id)
    return ResearchPlanResponse.model_validate(approved)


@router.post(
    "/research-plans/{plan_id}/promote",
    status_code=status.HTTP_200_OK,
)
def promote_research_plan_items(
    plan_id: int,
    promote_data: ResearchPlanPromote,
    db: DbSession,
) -> dict[str, list[int]]:
    plan = repository.get_plan(db, plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ResearchPlan #{plan_id} not found",
        )

    content = plan.content or {}
    promoted_questions: list[int] = []
    promoted_hypotheses: list[int] = []

    # Collect questions from plan
    all_plan_questions = []
    primary_q = content.get("primary_research_question", "")
    if primary_q:
        all_plan_questions.append(primary_q)
    for sq in content.get("secondary_research_questions", []):
        if sq and sq not in all_plan_questions:
            all_plan_questions.append(sq)

    # Promote selected questions with normalized duplicate protection
    for idx in promote_data.question_indices:
        if 0 <= idx < len(all_plan_questions):
            q_text = str(all_plan_questions[idx]).strip()
            existing_q = (
                db.query(ResearchQuestion)
                .filter(
                    ResearchQuestion.project_id == plan.project_id,
                    ResearchQuestion.question == q_text,
                )
                .first()
            )
            if existing_q:
                if existing_q.id not in promoted_questions:
                    promoted_questions.append(existing_q.id)
            else:
                new_q = ResearchQuestion(
                    project_id=plan.project_id,
                    question=q_text,
                    source="brainstorming",
                    brainstorming_session_id=plan.brainstorming_session_id,
                    status="open",
                )
                db.add(new_q)
                db.commit()
                db.refresh(new_q)
                promoted_questions.append(new_q.id)

    # Promote selected hypotheses with normalized duplicate protection
    plan_hypotheses = content.get("candidate_hypotheses", [])
    target_q_id = promote_data.target_question_id
    if target_q_id is None and promoted_questions:
        target_q_id = promoted_questions[0]
    elif target_q_id is None:
        first_q = (
            db.query(ResearchQuestion)
            .filter(ResearchQuestion.project_id == plan.project_id)
            .first()
        )
        if first_q:
            target_q_id = first_q.id

    if target_q_id:
        target_q = db.get(ResearchQuestion, target_q_id)
        if target_q:
            for idx in promote_data.hypothesis_indices:
                if 0 <= idx < len(plan_hypotheses):
                    h_text = str(plan_hypotheses[idx]).strip()
                    existing_h = (
                        db.query(Hypothesis)
                        .filter(
                            Hypothesis.question_id == target_q_id,
                            Hypothesis.statement == h_text,
                        )
                        .first()
                    )
                    if existing_h:
                        if existing_h.id not in promoted_hypotheses:
                            promoted_hypotheses.append(existing_h.id)
                    else:
                        new_h = Hypothesis(
                            question_id=target_q_id,
                            statement=h_text,
                            source="brainstorming",
                            brainstorming_session_id=plan.brainstorming_session_id,
                            status="proposed",
                        )
                        db.add(new_h)
                        db.commit()
                        db.refresh(new_h)
                        promoted_hypotheses.append(new_h.id)

    return {
        "promoted_question_ids": promoted_questions,
        "promoted_hypothesis_ids": promoted_hypotheses,
    }


@router.patch(
    "/research-plans/{plan_id}/archive",
    response_model=ResearchPlanResponse,
)
def archive_research_plan(
    plan_id: int,
    db: DbSession,
) -> ResearchPlanResponse:
    plan = repository.get_plan(db, plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ResearchPlan #{plan_id} not found",
        )
    archived = repository.set_plan_status(db, plan, "archived")
    return ResearchPlanResponse.model_validate(archived)


@router.patch(
    "/research-plans/{plan_id}/unarchive",
    response_model=ResearchPlanResponse,
)
def unarchive_research_plan(
    plan_id: int,
    db: DbSession,
) -> ResearchPlanResponse:
    plan = repository.get_plan(db, plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ResearchPlan #{plan_id} not found",
        )
    active = repository.set_plan_status(db, plan, "draft")
    return ResearchPlanResponse.model_validate(active)

