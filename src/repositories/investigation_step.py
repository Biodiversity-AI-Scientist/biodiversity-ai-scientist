from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.models.investigation_step import (
    InvestigationPlanGeneration,
    InvestigationStep,
    InvestigationStepDependency,
)
from src.models.scientific_capability import (
    CapabilityGap,
    CapabilitySelection,
    ScientificCapability,
)
from src.schemas.investigation_step import (
    InvestigationDAGEdge,
    InvestigationDAGNode,
    InvestigationDAGResponse,
    InvestigationStepCreate,
    InvestigationStepResponse,
    InvestigationStepStatus,
    InvestigationStepUpdate,
)



def check_for_cycle(nodes: list[str | int], edges: list[tuple[str | int, str | int]]) -> bool:
    """
    Returns True if a directed cycle exists among the given nodes and edges (Kahn's algorithm).
    Edges are (prerequisite, dependent) -> prerequisite must complete before dependent.
    """
    in_degree: dict[str | int, int] = {n: 0 for n in nodes}
    adj: dict[str | int, list[str | int]] = {n: [] for n in nodes}

    for u, v in edges:
        if u in adj and v in in_degree:
            adj[u].append(v)
            in_degree[v] += 1

    queue = deque([n for n in nodes if in_degree[n] == 0])
    visited_count = 0

    while queue:
        u = queue.popleft()
        visited_count += 1
        for v in adj[u]:
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)

    return visited_count != len(nodes)


class InvestigationStepRepository:
    @staticmethod
    def create_generation(
        db: Session,
        project_id: int,
        question_id: int,
        research_plan_id: int | None,
        summary_rationale: str | None,
        identified_uncertainties: list[Any] | None,
        model_provenance: dict[str, Any] | None,
        context_summary: dict[str, Any] | None,
    ) -> InvestigationPlanGeneration:
        gen = InvestigationPlanGeneration(
            project_id=project_id,
            question_id=question_id,
            research_plan_id=research_plan_id,
            summary_rationale=summary_rationale,
            identified_uncertainties=identified_uncertainties,
            model_provenance=model_provenance,
            context_summary=context_summary,
        )
        db.add(gen)
        db.flush()
        return gen

    @staticmethod
    def get_generation(db: Session, generation_id: int) -> InvestigationPlanGeneration | None:
        return db.get(InvestigationPlanGeneration, generation_id)

    @staticmethod
    def list_generations_for_question(db: Session, question_id: int) -> list[InvestigationPlanGeneration]:
        stmt = (
            select(InvestigationPlanGeneration)
            .where(InvestigationPlanGeneration.question_id == question_id)
            .order_by(desc(InvestigationPlanGeneration.id))
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def create_step(
        db: Session,
        project_id: int,
        question_id: int,
        data: InvestigationStepCreate,
        generation_id: int | None = None,
        research_plan_id: int | None = None,
    ) -> InvestigationStep:
        step = InvestigationStep(
            project_id=project_id,
            question_id=question_id,
            research_plan_id=research_plan_id,
            generation_id=generation_id,
            title=data.title,
            scientific_goal=data.scientific_goal,
            rationale=data.rationale,
            step_type=data.step_type,
            requires_capability=data.requires_capability,
            requires_experiment=data.requires_experiment,
            required_operation=data.required_operation,
            expected_evidence=data.expected_evidence,
            completion_criteria=data.completion_criteria,
            display_order=data.display_order,
            status=data.status.value if isinstance(data.status, InvestigationStepStatus) else data.status,
            researcher_notes=data.researcher_notes,
        )
        db.add(step)
        db.flush()

        for prereq_id in data.prerequisite_step_ids:
            dep = InvestigationStepDependency(
                step_id=step.id,
                depends_on_step_id=prereq_id,
            )
            db.add(dep)
        db.flush()
        return step

    @staticmethod
    def get_step(db: Session, step_id: int) -> InvestigationStep | None:
        return db.get(InvestigationStep, step_id)

    @staticmethod
    def list_steps_for_question(
        db: Session,
        question_id: int,
        include_archived: bool = False,
        status: str | None = None,
        generation_id: int | None = None,
    ) -> list[InvestigationStep]:
        stmt = select(InvestigationStep).where(InvestigationStep.question_id == question_id)
        if not include_archived:
            stmt = stmt.where(InvestigationStep.archived_at.is_(None))
        if status:
            stmt = stmt.where(InvestigationStep.status == status)
        if generation_id is not None:
            stmt = stmt.where(InvestigationStep.generation_id == generation_id)
        stmt = stmt.order_by(InvestigationStep.display_order.asc(), InvestigationStep.id.asc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_dependencies_for_question(
        db: Session, question_id: int
    ) -> tuple[dict[int, list[int]], dict[int, list[int]]]:
        """
        Returns (prereqs_map, dependents_map)
        prereqs_map[step_id] = [list of depends_on_step_ids]
        dependents_map[step_id] = [list of step_ids that depend on this step]
        """
        stmt = (
            select(InvestigationStepDependency)
            .join(InvestigationStep, InvestigationStepDependency.step_id == InvestigationStep.id)
            .where(InvestigationStep.question_id == question_id)
        )
        deps = list(db.scalars(stmt).all())

        prereqs_map: dict[int, list[int]] = defaultdict(list)
        dependents_map: dict[int, list[int]] = defaultdict(list)

        for d in deps:
            prereqs_map[d.step_id].append(d.depends_on_step_id)
            dependents_map[d.depends_on_step_id].append(d.step_id)

        return prereqs_map, dependents_map

    @classmethod
    def compute_step_response(
        cls,
        step: InvestigationStep,
        prereqs_map: dict[int, list[int]],
        dependents_map: dict[int, list[int]],
        all_steps_by_id: dict[int, InvestigationStep],
        selections_map: dict[int, CapabilitySelection] | None = None,
        gaps_map: dict[int, CapabilityGap] | None = None,
    ) -> InvestigationStepResponse:
        prereq_ids = prereqs_map.get(step.id, [])
        dependent_ids = dependents_map.get(step.id, [])

        sel = selections_map.get(step.id) if selections_map else None
        gap = gaps_map.get(step.id) if gaps_map else None

        # Multi-factor readiness
        readiness_state = "ready"
        is_blocked = False

        if step.status in (InvestigationStepStatus.COMPLETED.value, InvestigationStepStatus.SKIPPED.value, InvestigationStepStatus.REJECTED.value):
            readiness_state = "ready"
            is_blocked = False
        else:
            dep_blocked = False
            for pid in prereq_ids:
                p_step = all_steps_by_id.get(pid)
                if p_step and p_step.archived_at is None:
                    if p_step.status != InvestigationStepStatus.COMPLETED.value:
                        dep_blocked = True
                        break

            cap_blocked = False
            if step.requires_capability:
                if not sel or sel.selection_method == "none_adequate" or sel.selected_capability_id is None:
                    cap_blocked = True
                if gap and gap.status in ("unresolved", "in_progress"):
                    cap_blocked = True

            if dep_blocked:
                readiness_state = "dependency_blocked"
                is_blocked = True
            elif cap_blocked:
                readiness_state = "capability_blocked"
                is_blocked = True
            else:
                readiness_state = "ready"
                is_blocked = False

        cap_sel_id = sel.id if sel else None
        sel_cap_id = sel.selected_capability_id if sel else None
        sel_cap_key = sel.selected_capability.capability_key if (sel and sel.selected_capability) else None
        sel_cap_name = sel.selected_capability.display_name if (sel and sel.selected_capability) else None
        has_gap = bool(gap and gap.status in ("unresolved", "in_progress"))

        return InvestigationStepResponse(
            id=step.id,
            project_id=step.project_id,
            question_id=step.question_id,
            research_plan_id=step.research_plan_id,
            generation_id=step.generation_id,
            title=step.title,
            scientific_goal=step.scientific_goal,
            rationale=step.rationale,
            step_type=step.step_type,
            requires_capability=step.requires_capability,
            requires_experiment=step.requires_experiment,
            required_operation=step.required_operation,
            expected_evidence=step.expected_evidence,
            completion_criteria=step.completion_criteria,
            display_order=step.display_order,
            status=step.status,
            is_blocked=is_blocked,
            readiness_state=readiness_state,
            capability_selection_id=cap_sel_id,
            selected_capability_id=sel_cap_id,
            selected_capability_key=sel_cap_key,
            selected_capability_display_name=sel_cap_name,
            has_capability_gap=has_gap,
            prerequisite_step_ids=prereq_ids,
            dependent_step_ids=dependent_ids,
            researcher_notes=step.researcher_notes,
            archived_at=step.archived_at,
            created_at=step.created_at,
            updated_at=step.updated_at,
        )

    @staticmethod
    def list_step_responses_for_question(
        db: Session,
        question_id: int,
        include_archived: bool = False,
        status: str | None = None,
        generation_id: int | None = None,
    ) -> list[InvestigationStepResponse]:
        steps = InvestigationStepRepository.list_steps_for_question(
            db, question_id, include_archived=include_archived, status=status, generation_id=generation_id
        )
        if not steps:
            return []

        step_ids = [s.id for s in steps]
        prereqs_map, dependents_map = InvestigationStepRepository.get_dependencies_for_question(db, question_id)
        steps_by_id = {s.id: s for s in steps}

        # Fetch capability selections & gaps
        selections = (
            db.query(CapabilitySelection)
            .filter(CapabilitySelection.investigation_step_id.in_(step_ids))
            .all()
        )
        selections_map = {s.investigation_step_id: s for s in selections}

        gaps = (
            db.query(CapabilityGap)
            .filter(CapabilityGap.investigation_step_id.in_(step_ids))
            .all()
        )
        gaps_map = {g.investigation_step_id: g for g in gaps}

        return [
            InvestigationStepRepository.compute_step_response(
                s, prereqs_map, dependents_map, steps_by_id, selections_map, gaps_map
            )
            for s in steps
        ]

    @staticmethod
    def list_step_responses_for_project(
        db: Session,
        project_id: int,
        include_archived: bool = False,
    ) -> list[InvestigationStepResponse]:
        stmt = select(InvestigationStep).where(InvestigationStep.project_id == project_id)
        if not include_archived:
            stmt = stmt.where(InvestigationStep.archived_at.is_(None))
        stmt = stmt.order_by(InvestigationStep.display_order.asc(), InvestigationStep.id.asc())
        steps = list(db.scalars(stmt).all())
        if not steps:
            return []

        step_ids = [s.id for s in steps]
        dep_stmt = select(InvestigationStepDependency).where(
            (InvestigationStepDependency.step_id.in_(step_ids))
            | (InvestigationStepDependency.depends_on_step_id.in_(step_ids))
        )
        deps = list(db.scalars(dep_stmt).all())
        prereqs_map: dict[int, list[int]] = {s.id: [] for s in steps}
        dependents_map: dict[int, list[int]] = {s.id: [] for s in steps}
        for d in deps:
            if d.step_id in prereqs_map:
                prereqs_map[d.step_id].append(d.depends_on_step_id)
            if d.depends_on_step_id in dependents_map:
                dependents_map[d.depends_on_step_id].append(d.step_id)

        steps_by_id = {s.id: s for s in steps}

        # Fetch capability selections & gaps
        selections = (
            db.query(CapabilitySelection)
            .filter(CapabilitySelection.investigation_step_id.in_(step_ids))
            .all()
        )
        selections_map = {s.investigation_step_id: s for s in selections}

        gaps = (
            db.query(CapabilityGap)
            .filter(CapabilityGap.investigation_step_id.in_(step_ids))
            .all()
        )
        gaps_map = {g.investigation_step_id: g for g in gaps}

        return [
            InvestigationStepRepository.compute_step_response(
                s, prereqs_map, dependents_map, steps_by_id, selections_map, gaps_map
            )
            for s in steps
        ]



    @staticmethod
    def update_step(
        db: Session,
        step_id: int,
        data: InvestigationStepUpdate,
    ) -> InvestigationStep | None:
        step = db.get(InvestigationStep, step_id)
        if not step:
            return None

        update_dict = data.model_dump(exclude_unset=True)
        for key, val in update_dict.items():
            if val is not None:
                if key == "status" and isinstance(val, InvestigationStepStatus):
                    setattr(step, key, val.value)
                else:
                    setattr(step, key, val)

        db.flush()
        return step

    @staticmethod
    def delete_or_archive_step(db: Session, step_id: int) -> bool:
        step = db.get(InvestigationStep, step_id)
        if not step:
            return False

        # Hard delete allowed for never-approved proposed steps
        if step.status == InvestigationStepStatus.PROPOSED.value and step.archived_at is None:
            db.delete(step)
            db.flush()
            return True
        else:
            # Soft archive for approved / historical steps
            step.archived_at = datetime.now(timezone.utc)
            db.flush()
            return True

    @staticmethod
    def add_dependency(db: Session, step_id: int, depends_on_step_id: int) -> InvestigationStepDependency:
        if step_id == depends_on_step_id:
            raise ValueError("A step cannot depend on itself.")

        step = db.get(InvestigationStep, step_id)
        dep_step = db.get(InvestigationStep, depends_on_step_id)
        if not step or not dep_step:
            raise ValueError("One or both steps not found.")

        # Check existing
        existing = (
            db.query(InvestigationStepDependency)
            .filter_by(step_id=step_id, depends_on_step_id=depends_on_step_id)
            .first()
        )
        if existing:
            return existing

        # Cycle check
        all_steps = (
            db.query(InvestigationStep)
            .filter(InvestigationStep.question_id == step.question_id)
            .all()
        )
        nodes = [s.id for s in all_steps]
        all_deps = (
            db.query(InvestigationStepDependency)
            .join(InvestigationStep, InvestigationStepDependency.step_id == InvestigationStep.id)
            .where(InvestigationStep.question_id == step.question_id)
            .all()
        )
        edges = [(d.depends_on_step_id, d.step_id) for d in all_deps]
        edges.append((depends_on_step_id, step_id))

        if check_for_cycle(nodes, edges):
            raise ValueError("Adding this dependency would introduce a circular dependency cycle in the DAG.")

        dep = InvestigationStepDependency(
            step_id=step_id,
            depends_on_step_id=depends_on_step_id,
        )
        db.add(dep)
        db.flush()
        return dep

    @staticmethod
    def remove_dependency(db: Session, step_id: int, depends_on_step_id: int) -> bool:
        dep = (
            db.query(InvestigationStepDependency)
            .filter_by(step_id=step_id, depends_on_step_id=depends_on_step_id)
            .first()
        )
        if dep:
            db.delete(dep)
            db.flush()
            return True
        return False

    @classmethod
    def get_dag_for_question(cls, db: Session, question_id: int) -> InvestigationDAGResponse:
        steps = cls.list_step_responses_for_question(db, question_id, include_archived=False)
        nodes: list[InvestigationDAGNode] = []
        edges: list[InvestigationDAGEdge] = []

        approved_cnt = 0
        completed_cnt = 0
        blocked_cnt = 0

        for s in steps:
            if s.status == InvestigationStepStatus.APPROVED.value:
                approved_cnt += 1
            if s.status == InvestigationStepStatus.COMPLETED.value:
                completed_cnt += 1
            if s.is_blocked:
                blocked_cnt += 1

            nodes.append(
                InvestigationDAGNode(
                    id=s.id,
                    title=s.title,
                    step_type=s.step_type,
                    status=s.status,
                    is_blocked=s.is_blocked,
                    readiness_state=s.readiness_state,
                    requires_capability=s.requires_capability,
                    requires_experiment=s.requires_experiment,
                    selected_capability_key=s.selected_capability_key,
                    has_capability_gap=s.has_capability_gap,
                    display_order=s.display_order,
                )
            )


            for pid in s.prerequisite_step_ids:
                edges.append(InvestigationDAGEdge(from_step_id=pid, to_step_id=s.id))

        return InvestigationDAGResponse(
            question_id=question_id,
            nodes=nodes,
            edges=edges,
            total_steps=len(steps),
            approved_steps=approved_cnt,
            completed_steps=completed_cnt,
            blocked_steps=blocked_cnt,
        )
