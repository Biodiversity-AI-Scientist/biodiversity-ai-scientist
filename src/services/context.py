import re
from typing import Any
from sqlalchemy import text
from sqlalchemy.orm import Session
from src.models import (
    BrainstormingSession,
    Hypothesis,
    ResearchProject,
    ResearchQuestion,
)
from src.services.data_intelligence import (
    get_existing_model_networks,
    get_genus_image_counts,
    get_species_image_counts,
    get_taxon_image_summary,
    get_top_unmodeled_genera,
)
from src.services.scientific_context import ScientificContextService



def extract_potential_taxa(text_corpus: str) -> list[str]:
    """Extracts candidate taxonomic words (genera, families ending in -idae, orders/classes/phyla) from text."""
    # Match family names (e.g. Strombidae, Conidae, Muricidae)
    families = re.findall(r"\b([A-Z][a-z]+idae)\b", text_corpus)
    # Match higher taxa
    higher_taxa = re.findall(r"\b(Mollusca|Gastropoda|Bivalvia|Cephalopoda|Scaphopoda|Polyplacophora)\b", text_corpus, re.IGNORECASE)
    # Match genus names or capitalized biological terms
    genera = re.findall(r"\b([A-Z][a-z]{2,20})\b", text_corpus)

    candidates = []
    for ht in higher_taxa:
        ht_cap = ht.capitalize()
        if ht_cap not in candidates:
            candidates.append(ht_cap)
    for f in families:
        if f not in candidates:
            candidates.append(f)
    for g in genera:
        # Filter out common English capitalized words
        if g not in candidates and g.lower() not in {
            "the", "which", "what", "how", "can", "should", "does", "are", "project",
            "study", "research", "initial", "classifier", "model", "analysis", "dataset",
            "morphometrics", "phylogeography", "objective", "session", "user", "assistant",
            "candidate", "feasible", "genera", "species", "taxon", "database", "material",
            "recommend", "evaluation", "question", "hypothesis", "training", "marine",
            "mollusk", "mollusks", "phylum", "class", "family", "order",
        }:
            candidates.append(g)

    return candidates[:6]


def get_all_modeled_taxa_summary(dwh_db: Session) -> list[str]:
    """Fetches list of distinct taxa that already have models in DWH.ModelNetwork."""
    try:
        sql = text("SELECT DISTINCT Taxon FROM ModelNetwork WHERE Taxon IS NOT NULL AND Taxon != '' ORDER BY Taxon ASC")
        rows = dwh_db.execute(sql).fetchall()
        return [r[0] for r in rows if r[0]]
    except Exception:
        return []


def build_data_intelligence_context(
    dwh_db: Session | None,
    query_text: str,
) -> str:
    """Queries DWH on Server 112 for factual empirical profiles, existing models in ModelNetwork, and novel candidate genera."""
    if not dwh_db:
        return ""

    context_sections = []

    # 1. Top Recommended Unmodeled Candidate Genera (for novel classifier queries)
    is_marine = bool(re.search(r"\bmarine\b", query_text, re.IGNORECASE))
    class_match = re.search(r"\b(Gastropoda|Bivalvia|Cephalopoda)\b", query_text, re.IGNORECASE)
    matched_class = class_match.group(1).capitalize() if class_match else None

    unmodeled = get_top_unmodeled_genera(
        dwh_db,
        marine_only=is_marine or True,  # default to marine focus for malacology
        class_name=matched_class,
        limit=12,
    )
    if unmodeled:
        lines = ["=== RECOMMENDED NOVEL CANDIDATE GENERA IN DWH (Unmodeled, Ready for New Classifiers) ==="]
        lines.append("The following genera have substantial image collections in DWH and NO existing models in ModelNetwork:")
        for u in unmodeled:
            lines.append(
                f"  - Genus {u['genus_name']} (Family: {u['family_name'] or 'N/A'}, Class: {u['class_name'] or 'N/A'}): "
                f"{u['total_images']} total images in DWH [FEASIBLE NOVEL TARGET]"
            )
        context_sections.append("\n".join(lines))

    # 2. Existing ModelNetwork Inventory Summary (Explicit DO NOT RECOMMEND AS NOVEL list)
    modeled_taxa = get_all_modeled_taxa_summary(dwh_db)
    if modeled_taxa:
        sample_display = ", ".join(modeled_taxa[:50])
        context_sections.append(
            f"=== TAXA WITH EXISTING TRAINED MODELS IN DWH (DWH.ModelNetwork: {len(modeled_taxa)} Taxa) ===\n"
            f"Models Already Exist For: {sample_display} ...\n"
            f"CRITICAL CONSTRAINT: Do NOT recommend any of these already modeled genera (e.g. Conus, Harpa, Morum, Nerita, Nucula, Oliva, Pecten, Strombus, Turritella, Vexillum, Zoila) "
            f"as candidate targets for a 'new' classification model. Propose ONLY from the unmodeled candidate genera above."
        )

    # 3. Specific Taxon Deep Dive if specific taxa/families are mentioned in query
    taxa = extract_potential_taxa(query_text)
    for taxon in taxa:
        try:
            is_higher_taxa = taxon.lower() in ("mollusca", "gastropoda", "bivalvia", "cephalopoda")
            if taxon.endswith("idae"):
                genus_summaries = get_genus_image_counts(
                    dwh_db,
                    family_name=taxon,
                    min_species=2,
                    min_images_per_species=5,
                )

                if genus_summaries:
                    with_models = [g for g in genus_summaries if g.has_existing_model]
                    novel_candidates = [g for g in genus_summaries if not g.has_existing_model and g.is_feasible_for_classifier]

                    lines = [f"\n=== Detailed Family Profile: {taxon} (DWH Material & Model Registry) ==="]
                    lines.append(f"Total Evaluated Genera: {len(genus_summaries)}")

                    if with_models:
                        lines.append(f"Genera with Existing Models in DWH.ModelNetwork ({len(with_models)} genera):")
                        for g in with_models[:6]:
                            views_str = ", ".join(g.existing_model_views) if g.existing_model_views else "Default"
                            lines.append(
                                f"  - [EXISTING MODEL] Genus {g.genus_name}: {g.species_above_threshold}/{g.total_species} species >=5 imgs, "
                                f"{g.total_images} imgs (Model Views: {views_str})"
                            )

                    if novel_candidates:
                        lines.append(f"Prime Novel Candidates without Existing Models (Ready for New Classifier Training):")
                        for g in novel_candidates[:8]:
                            lines.append(
                                f"  - [NOVEL CANDIDATE] Genus {g.genus_name}: {g.species_above_threshold}/{g.total_species} species >=5 imgs, "
                                f"{g.total_images} total imgs, imbalance: {g.imbalance_ratio}x [FEASIBLE]"
                            )
                    context_sections.append("\n".join(lines))
            elif not is_higher_taxa:
                # Single Genus lookup
                summary = get_taxon_image_summary(dwh_db, taxon_name=taxon)
                if summary.total_species > 0 or summary.total_images > 0 or summary.existing_models:
                    species_counts = get_species_image_counts(dwh_db, genus_name=taxon, min_images=5)
                    feasible_species_cnt = sum(1 for sc in species_counts if sc.meets_threshold)

                    lines = [f"\n=== Detailed Taxon: {summary.taxon_name} (Rank: {summary.rank}) ==="]
                    lines.append(
                        f"Database Material: {summary.total_images} total images across {summary.total_species} species "
                        f"({summary.species_with_images} species with >=1 image; {feasible_species_cnt} species with >=5 images)."
                    )
                    if summary.view_distribution:
                        views_str = ", ".join(f"{v}: {cnt}" for v, cnt in summary.view_distribution.items())
                        lines.append(f"Available Viewpoints: {views_str}")
                    if summary.source_distribution:
                        top_sources = sorted(summary.source_distribution.items(), key=lambda x: x[1], reverse=True)[:4]
                        src_str = ", ".join(f"{s}: {cnt}" for s, cnt in top_sources)
                        lines.append(f"Data Sources: {src_str}")

                    if summary.existing_models:
                        model_descriptions = []
                        for m in summary.existing_models:
                            v_str = f" ({m.view_type})" if m.view_type else ""
                            model_descriptions.append(f"{m.model_path}{v_str}")
                        lines.append(f"Existing Models in DWH.ModelNetwork: {'; '.join(model_descriptions)}")
                    else:
                        lines.append("Existing Models in DWH.ModelNetwork: None (This is a novel unmodeled genus)")

                    context_sections.append("\n".join(lines))
        except Exception:
            continue

    return "\n\n".join(context_sections)


def build_brainstorming_context(
    db: Session,
    project_id: int,
    session_id: int | None = None,
    dwh_db: Session | None = None,
    latest_user_message: str | None = None,
) -> dict[str, Any]:
    project = db.get(ResearchProject, project_id)
    project_title = project.title if project else f"Project #{project_id}"
    project_desc = getattr(project, "description", "") or getattr(project, "objective", "") or ""

    questions = (
        db.query(ResearchQuestion)
        .filter(ResearchQuestion.project_id == project_id)
        .all()
    )
    q_summaries = [f"Q{q.id}: {q.question}" for q in questions]

    hypotheses = (
        db.query(Hypothesis)
        .join(ResearchQuestion, Hypothesis.question_id == ResearchQuestion.id)
        .filter(ResearchQuestion.project_id == project_id)
        .all()
    )
    h_summaries = [f"H{h.id} (Q{h.question_id}): {h.statement}" for h in hypotheses]

    session_summary = ""
    history_turns = []
    initial_idea = ""
    if session_id:
        session = db.get(BrainstormingSession, session_id)
        if session:
            initial_idea = session.initial_idea or ""
            msgs = session.messages or []
            for m in msgs:
                role_label = str(m.get("role", "user")).capitalize()
                content = str(m.get("content", ""))
                turn_str = f"[{role_label}]: {content}"
                history_turns.append(turn_str)
            session_summary = "\n".join(history_turns)

    # Assemble text corpus for biological entity extraction
    corpus_parts = [project_title, project_desc, initial_idea]
    if latest_user_message:
        corpus_parts.append(latest_user_message)
    if history_turns:
        corpus_parts.extend(history_turns[-3:])  # include last 3 turns
    full_corpus = " ".join(corpus_parts)

    # Adaptive Orchestration: Assemble ResearchIntelligencePacket with 4-way provenance
    from src.services.orchestrator import (
        assemble_intelligence_packet,
        format_packet_for_llm_prompt,
    )

    project_ctx = {
        "title": project_title,
        "objective": project_desc,
        "existing_questions_count": len(q_summaries),
        "existing_hypotheses_count": len(h_summaries),
    }

    packet = assemble_intelligence_packet(
        db=db,
        dwh_db=dwh_db,
        project_id=project_id,
        user_query=full_corpus,
        project_context=project_ctx,
    )
    final_intel_context = format_packet_for_llm_prompt(packet)

    focal_taxa = extract_potential_taxa(full_corpus)
    from src.services.research_program import build_research_program_summary
    research_program_context = build_research_program_summary(db, focal_taxa=focal_taxa)

    from src.services.domain_intelligence import (
        format_domain_intelligence_for_prompt,
        get_taxon_domain_intelligence,
    )
    domain_contexts = []
    for ft in focal_taxa[:2]:
        try:
            d_ctx = get_taxon_domain_intelligence(ft)
            domain_contexts.append(format_domain_intelligence_for_prompt(d_ctx))
        except Exception:
            pass
    domain_intel_text = "\n\n".join(domain_contexts)

    # Capability Registry context for future LLM reasoning
    capabilities_text = build_capabilities_summary(db)

    return {
        "project_title": project_title,
        "project_description": project_desc,
        "initial_idea": initial_idea,
        "existing_questions": "\n".join(q_summaries),
        "existing_hypotheses": "\n".join(h_summaries),
        "existing_questions_list": q_summaries,
        "existing_hypotheses_list": h_summaries,
        "conversation_summary": session_summary,
        "history_turns": history_turns,
        "data_intelligence_context": final_intel_context,
        "research_program_context": research_program_context,
        "domain_intelligence_context": domain_intel_text,
        "capabilities_context": capabilities_text,
        "intelligence_packet": packet.model_dump(),
    }


def build_capabilities_summary(db: Session | None) -> str:
    """Builds a structured markdown summary of available registered capabilities for LLM context."""
    if not db:
        return ""
    try:
        from src.repositories.scientific_capability import list_capabilities
        caps = list_capabilities(db, enabled_only=True)
        if not caps:
            return ""
        lines = ["=== AVAILABLE REGISTERED SCIENTIFIC CAPABILITIES ==="]
        for c in caps:
            app_name = c.application.display_name if c.application else "Local Tool"
            lines.append(f"- [{c.capability_key}] {c.display_name} (App: {app_name}, Duration: {c.typical_duration or 'N/A'}, Repro: {c.reproducibility_level})")
            lines.append(f"  Purpose: {c.scientific_purpose}")
        return "\n".join(lines)
    except Exception:
        return ""




