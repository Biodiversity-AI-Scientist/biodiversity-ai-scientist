from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.database import get_db, get_dwh_db
from src.models import ResearchQuestion
from src.repositories.investigation_step import InvestigationStepRepository
from src.schemas.investigation_step import (
    InvestigationDAGResponse,
    InvestigationPlanGenerateRequest,
    InvestigationPlanGenerationResponse,
    InvestigationStepCreate,
    InvestigationStepResponse,
    InvestigationStepUpdate,
)
from src.services.investigation_planning import InvestigationPlanningService

router = APIRouter(
    tags=["Investigation Planning & Step Sequencing (Phase 8)"],
)

DbSession = Annotated[
    Session,
    Depends(get_db),
]

DwhSession = Annotated[
    Session | None,
    Depends(get_dwh_db),
]


@router.post(
    "/questions/{question_id}/investigation-plan/generate",
    response_model=InvestigationPlanGenerationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a structured DAG of InvestigationSteps using LLM Planning Engine",
)
def generate_investigation_plan(
    question_id: int,
    req: InvestigationPlanGenerateRequest,
    db: DbSession,
    dwh_db: DwhSession = None,
):
    try:
        return InvestigationPlanningService.generate_plan_for_question(
            db=db,
            dwh_db=dwh_db,
            question_id=question_id,
            research_plan_id=req.research_plan_id,
            user_guidance=req.user_guidance,
            focus_areas=req.focus_areas,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Investigation plan generation failed: {e}",
        )


@router.get(
    "/questions/{question_id}/investigation-plan/generations",
    response_model=list[InvestigationPlanGenerationResponse],
    summary="List historical generation batches for a ResearchQuestion",
)
def list_investigation_generations(
    question_id: int,
    db: DbSession,
):
    generations = InvestigationStepRepository.list_generations_for_question(db, question_id)
    prereqs_map, dependents_map = InvestigationStepRepository.get_dependencies_for_question(db, question_id)
    
    all_steps = InvestigationStepRepository.list_steps_for_question(db, question_id, include_archived=True)
    steps_by_id = {s.id: s for s in all_steps}

    results = []
    for g in generations:
        gen_steps = [s for s in all_steps if s.generation_id == g.id]
        step_resps = [
            InvestigationStepRepository.compute_step_response(s, prereqs_map, dependents_map, steps_by_id)
            for s in gen_steps
        ]
        results.append(
            InvestigationPlanGenerationResponse(
                id=g.id,
                project_id=g.project_id,
                question_id=g.question_id,
                research_plan_id=g.research_plan_id,
                summary_rationale=g.summary_rationale,
                identified_uncertainties=g.identified_uncertainties,
                model_provenance=g.model_provenance,
                context_summary=g.context_summary,
                created_at=g.created_at,
                steps_count=len(step_resps),
                steps=step_resps,
            )
        )
    return results


@router.get(
    "/questions/{question_id}/investigation-steps",
    response_model=list[InvestigationStepResponse],
    summary="List all InvestigationSteps for a question with computed blocked status",
)
def list_investigation_steps(
    question_id: int,
    db: DbSession,
    include_archived: bool = Query(default=False),
    generation_id: int | None = Query(default=None),
):
    return InvestigationStepRepository.list_step_responses_for_question(
        db=db,
        question_id=question_id,
        include_archived=include_archived,
        generation_id=generation_id,
    )


@router.get(
    "/projects/{project_id}/investigation-steps",
    response_model=list[InvestigationStepResponse],
    summary="List all InvestigationSteps for a project",
)
def list_project_investigation_steps(
    project_id: int,
    db: DbSession,
    include_archived: bool = Query(default=False),
):
    return InvestigationStepRepository.list_step_responses_for_project(
        db=db,
        project_id=project_id,
        include_archived=include_archived,
    )



@router.get(
    "/questions/{question_id}/investigation-steps/dag",
    response_model=InvestigationDAGResponse,
    summary="Get DAG visualization graph (nodes and edges) for a question",
)
def get_investigation_dag(
    question_id: int,
    db: DbSession,
):
    return InvestigationStepRepository.get_dag_for_question(db, question_id)


@router.post(
    "/questions/{question_id}/investigation-steps",
    response_model=InvestigationStepResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Manually create a single InvestigationStep",
)
def create_investigation_step(
    question_id: int,
    req: InvestigationStepCreate,
    db: DbSession,
):
    question = db.get(ResearchQuestion, question_id)
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Question {question_id} not found")

    step = InvestigationStepRepository.create_step(
        db=db,
        project_id=question.project_id,
        question_id=question_id,
        data=req,
    )
    db.commit()

    prereqs_map, dependents_map = InvestigationStepRepository.get_dependencies_for_question(db, question_id)
    all_steps = {s.id: s for s in InvestigationStepRepository.list_steps_for_question(db, question_id, include_archived=True)}
    return InvestigationStepRepository.compute_step_response(step, prereqs_map, dependents_map, all_steps)


@router.get(
    "/investigation-steps/{step_id}",
    response_model=InvestigationStepResponse,
    summary="Get single InvestigationStep by ID",
)
def get_investigation_step(
    step_id: int,
    db: DbSession,
):
    step = InvestigationStepRepository.get_step(db, step_id)
    if not step:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Step {step_id} not found")

    prereqs_map, dependents_map = InvestigationStepRepository.get_dependencies_for_question(db, step.question_id)
    all_steps = {s.id: s for s in InvestigationStepRepository.list_steps_for_question(db, step.question_id, include_archived=True)}
    return InvestigationStepRepository.compute_step_response(step, prereqs_map, dependents_map, all_steps)


@router.patch(
    "/investigation-steps/{step_id}",
    response_model=InvestigationStepResponse,
    summary="Update InvestigationStep fields, approval, or completion status",
)
def update_investigation_step(
    step_id: int,
    req: InvestigationStepUpdate,
    db: DbSession,
):
    step = InvestigationStepRepository.update_step(db, step_id, req)
    if not step:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Step {step_id} not found")
    db.commit()

    prereqs_map, dependents_map = InvestigationStepRepository.get_dependencies_for_question(db, step.question_id)
    all_steps = {s.id: s for s in InvestigationStepRepository.list_steps_for_question(db, step.question_id, include_archived=True)}
    return InvestigationStepRepository.compute_step_response(step, prereqs_map, dependents_map, all_steps)


@router.post(
    "/investigation-steps/{step_id}/dependencies",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Add prerequisite dependency edge",
)
def add_step_dependency(
    step_id: int,
    depends_on_step_id: int = Query(..., description="ID of prerequisite step that must complete first"),
    db: Session = Depends(get_db),
):
    try:
        dep = InvestigationStepRepository.add_dependency(db, step_id, depends_on_step_id)
        db.commit()
        return {"status": "created", "step_id": dep.step_id, "depends_on_step_id": dep.depends_on_step_id}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/investigation-steps/{step_id}/dependencies/{depends_on_step_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove prerequisite dependency edge",
)
def remove_step_dependency(
    step_id: int,
    depends_on_step_id: int,
    db: DbSession,
):
    removed = InvestigationStepRepository.remove_dependency(db, step_id, depends_on_step_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dependency edge not found")
    db.commit()


@router.delete(
    "/investigation-steps/{step_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete unapproved proposed step or archive historical step",
)
def delete_or_archive_step(
    step_id: int,
    db: DbSession,
):
    deleted = InvestigationStepRepository.delete_or_archive_step(db, step_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Step not found")
    db.commit()
