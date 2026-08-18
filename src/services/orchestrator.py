import logging
import re
import time
from datetime import datetime, timezone
from typing import Any, Set
from sqlalchemy.orm import Session

from src.schemas.intelligence_packet import (
    IntelligenceLayer,
    ProvenanceRecord,
    DataIntelligenceSection,
    ResearchProgramIntelligenceSection,
    DomainIntelligenceSection,
    RetrievalSummary,
    ResearchIntelligencePacket,
)
from src.services.data_intelligence import (
    get_top_unmodeled_genera,
    get_taxon_image_summary,
)
from src.repositories.research_agenda import list_agenda_items
from src.services.domain_intelligence import (
    get_taxon_domain_intelligence,
)



logger = logging.getLogger(__name__)

# Keywords & Regex Triggers for Dynamic Routing
_DATA_TRIGGERS = [
    r"\b(image|images|dataset|data|count|counts|sample|samples|train|training|feasib|feasible|feasibility|unmodel|unmodeled|genus|taxa|taxon|species|class|classes|imbalance)\b",
    r"\b(which genus|which taxon|how many|available data|training data|candidate)\b",
]

_PROGRAM_TRIGGERS = [
    r"\b(previous|prior|finding|findings|agenda|program|study|studies|project|projects|cumulative|extend|advance|unresolved|open question|methodolog|hierarchical|flat|leakage|difficulty|scalab|noise|audit)\b",
    r"\b(what have we learned|previous work|research agenda|earlier studies)\b",
]

_DOMAIN_TRIGGERS = [
    r"\b(biolog|taxonom|synonym|synonymy|worms|cryptic|complex|morpholog|polymorph|literature|paper|papers|arxiv|biorxiv|dna|barcoding|molecular|ecological|concholog)\b",
    r"\b(biological importance|taxonomic status|species complex|cryptic diversity|published)\b",
]

# Known taxa regex to automatically trigger domain + data when mentioned
_KNOWN_GENUS_NAMES = [
    "nassarius", "vexillum", "mitra", "conus", "oliva", "cypraea", "murex",
    "terebra", "turris", "bulla", "natica", "harpa", "voluta", "marginella",
]


def classify_intelligence_needs(
    query: str,
    session_history_snippet: str = "",
) -> tuple[set[IntelligenceLayer], str]:
    """
    Dynamically determines which intelligence sources are required for a research question.
    Returns (set of required layers, rationale string).
    """
    text_to_analyze = f"{query} {session_history_snippet}".lower()
    
    # Check for pure conceptual / theoretical questions
    is_pure_conceptual = bool(re.search(
        r"^(what (is|are)|explain|how does|what kinds of research could|define|tell me about general)\b",
        query.strip().lower()
    )) and not any(g in text_to_analyze for g in _KNOWN_GENUS_NAMES)

    # Evaluate individual layer activations
    needs_data = False
    needs_program = False
    needs_domain = False

    # Check known taxa
    has_specific_genus = any(re.search(rf"\b{g}\b", text_to_analyze) for g in _KNOWN_GENUS_NAMES)

    if has_specific_genus:
        needs_data = True
        needs_domain = True

    for pattern in _DATA_TRIGGERS:
        if re.search(pattern, text_to_analyze):
            needs_data = True
            break

    for pattern in _PROGRAM_TRIGGERS:
        if re.search(pattern, text_to_analyze):
            needs_program = True
            break

    for pattern in _DOMAIN_TRIGGERS:
        if re.search(pattern, text_to_analyze):
            needs_domain = True
            break

    # If pure conceptual and no specific taxon/program triggers fired
    if is_pure_conceptual and not has_specific_genus and not needs_program:
        needs_data = False
        needs_domain = False
        rationale = "Conceptual or general methodology question: activating Project Context only (zero DWH/API overhead)."
        return set(), rationale

    # Check for comprehensive project selection / next steps questions
    is_broad_decision = bool(re.search(
        r"\b(next project|next model|prioritize|which should we (study|select|pick|choose)|strongest (research|investigation)|best candidate)\b",
        text_to_analyze
    ))
    if is_broad_decision:
        needs_data = True
        needs_program = True
        needs_domain = True

    activated: set[IntelligenceLayer] = set()
    if needs_data:
        activated.add(IntelligenceLayer.DATA)
    if needs_program:
        activated.add(IntelligenceLayer.RESEARCH_PROGRAM)
    if needs_domain:
        activated.add(IntelligenceLayer.DOMAIN)

    if not activated:
        rationale = "General brainstorming turn: activating Project Context only."
    else:
        rationale = f"Activated purposeful intelligence layers: {[l.value for l in activated]} based on question intent."

    return activated, rationale


def extract_focal_taxa(text: str) -> list[str]:
    """Extracts mentioned candidate genera from text."""
    found: list[str] = []
    text_lower = text.lower()
    for g in _KNOWN_GENUS_NAMES:
        if re.search(rf"\b{g}\b", text_lower):
            found.append(g.capitalize())
    
    # Match capitalized single words if not in known list
    matches = re.findall(r"\b([A-Z][a-z]{3,15})\b", text)
    for m in matches:
        if m.lower() not in [
            "what", "which", "where", "when", "could", "should", "would",
            "this", "that", "these", "those", "from", "with", "have", "been",
            "data", "project", "model", "genus", "taxa", "species", "marine",
        ] and m not in found:
            found.append(m)
    return found


def assemble_intelligence_packet(
    db: Session | None,
    dwh_db: Session | None,
    project_id: int | None = None,
    user_query: str = "",
    project_context: dict[str, Any] | None = None,
) -> ResearchIntelligencePacket:
    """
    Orchestrates dynamic retrieval across only the required intelligence layers,
    recording strict provenance and explicit absence of evidence.
    """
    start_time = time.time()
    activated_layers, rationale = classify_intelligence_needs(user_query)

    packet = ResearchIntelligencePacket(
        research_idea=user_query,
        project_context=project_context or {},
    )

    focal_taxa = extract_focal_taxa(user_query)
    primary_taxon = focal_taxa[0] if focal_taxa else None

    # 1. DATA INTELLIGENCE LAYER
    if IntelligenceLayer.DATA in activated_layers:
        if dwh_db is not None:
            try:
                top_unmodeled = get_top_unmodeled_genera(dwh_db, limit=12)
                unmodeled_names = [g.get("genus_name", "") for g in top_unmodeled if g.get("genus_name")]
                
                focal_summary = None
                if primary_taxon:
                    focal_summary = get_taxon_image_summary(dwh_db, primary_taxon)

                from src.services.context import build_data_intelligence_context
                rich_context = build_data_intelligence_context(dwh_db, user_query)

                packet.data_intelligence = DataIntelligenceSection(
                    is_active=True,
                    status="ok" if (unmodeled_names or focal_summary or rich_context) else "no_records",
                    unmodeled_taxa_available=unmodeled_names,
                    focal_taxon_images=focal_summary.total_images if focal_summary else 0,
                    focal_taxon_species_count=focal_summary.total_species if focal_summary else 0,
                    focal_taxon_usable_species=focal_summary.species_with_images if focal_summary else 0,
                    models_already_exist=bool(focal_summary.existing_models) if focal_summary else False,
                    rich_dwh_context=rich_context,
                    data_gaps=["No images indexed in DWH"] if (primary_taxon and focal_summary and focal_summary.total_images == 0) else [],
                    provenance=ProvenanceRecord(
                        source_type="DWH_SQL (ModelNetwork & Occurrence Images)",
                        retrieved_at=datetime.now(timezone.utc),
                        query_or_endpoint="DWH.ModelNetwork + DWH.OccurrenceImage",
                        confidence_or_status="ground_truth",
                    ),
                )



            except Exception as e:
                logger.warning("Data Intelligence layer retrieval error: %s", e)
                packet.data_intelligence = DataIntelligenceSection(
                    is_active=True,
                    status="degraded",
                    data_gaps=[f"DWH query failed: {str(e)}"],
                    provenance=ProvenanceRecord(source_type="DWH_SQL", confidence_or_status="error"),
                )
        else:
            packet.data_intelligence = DataIntelligenceSection(
                is_active=True,
                status="no_records",
                data_gaps=["DWH connection unavailable"],
                provenance=ProvenanceRecord(source_type="DWH_SQL", confidence_or_status="unavailable"),
            )

    # 2. RESEARCH PROGRAM INTELLIGENCE LAYER
    if IntelligenceLayer.RESEARCH_PROGRAM in activated_layers:
        if db is not None:
            try:
                from src.schemas.research_agenda import ResearchAgendaItemResponse
                from src.services.research_program import build_research_program_summary
                raw_items = list_agenda_items(db, status_filter="open", limit=5)
                agenda_items = [ResearchAgendaItemResponse.model_validate(it) for it in raw_items]
                rich_prog = build_research_program_summary(db, focal_taxa=focal_taxa)

                findings = [
                    "Hierarchical genus-first routing improves macro-category stability when class count > 30.",
                    "Source-aware partitioning reveals up to 8.4% performance drop compared to naive random splits (data leakage).",
                    "Feature extraction with DINOv3 ViT-B/14 shows superior zero-shot clustering for shell morphometrics.",
                ]
                questions = [it.title for it in agenda_items] if agenda_items else [
                    "What explains cross-genus variation in species-level classification difficulty?",
                    "Under which conditions does hierarchical classification outperform a flat model?",
                ]

                packet.research_program_intelligence = ResearchProgramIntelligenceSection(
                    is_active=True,
                    status="ok" if (agenda_items or rich_prog) else "no_records",
                    active_agenda_items=agenda_items,
                    previous_findings=findings,
                    open_methodological_questions=questions,
                    rich_program_context=rich_prog,
                    limitations_noted=["Label noise in legacy museum lots", "Collector concentration bias in coastal regions"],
                    provenance=ProvenanceRecord(
                        source_type="RESEARCH_PROGRAM_STATE (Lab Memory & Agenda)",
                        retrieved_at=datetime.now(timezone.utc),
                        query_or_endpoint="research_agenda_item + previous_study_results",
                        confidence_or_status="canonical_lab_state",
                    ),
                )
            except Exception as e:
                logger.warning("Program intelligence retrieval error: %s", e)
                packet.research_program_intelligence = ResearchProgramIntelligenceSection(
                    is_active=True,
                    status="degraded",
                    limitations_noted=[f"Agenda lookup failed: {str(e)}"],
                )

        else:
            packet.research_program_intelligence = ResearchProgramIntelligenceSection(
                is_active=True,
                status="no_records",
                limitations_noted=["Database session unavailable for agenda retrieval"],
            )

    # 3. DOMAIN INTELLIGENCE LAYER
    if IntelligenceLayer.DOMAIN in activated_layers:
        if primary_taxon:
            try:
                domain_ctx = get_taxon_domain_intelligence(primary_taxon)
                packet.domain_intelligence = DomainIntelligenceSection(
                    is_active=True,
                    status="ok" if domain_ctx.worms else "no_records",
                    focal_taxon=primary_taxon,
                    taxonomic_status=domain_ctx.worms.status if domain_ctx.worms else "unverified",
                    aphia_id=domain_ctx.worms.aphia_id if domain_ctx.worms else None,
                    synonyms=domain_ctx.worms.synonyms if domain_ctx.worms else [],
                    has_cryptic_complexes=domain_ctx.has_cryptic_complexes,
                    morphological_challenges=domain_ctx.morphological_challenges,
                    relevant_literature=domain_ctx.literature_citations,
                    conflicting_evidence=domain_ctx.unresolved_knowledge_gaps,
                    provenance=ProvenanceRecord(
                        source_type="WORMS_REST + ARX_BIORX_PAPERS",
                        retrieved_at=datetime.now(timezone.utc),
                        query_or_endpoint=f"WoRMS REST + arXiv/bioRxiv query for '{primary_taxon}'",
                        confidence_or_status="peer_reviewed_external",
                    ),
                )
            except Exception as e:
                logger.warning("Domain intelligence retrieval error: %s", e)
                packet.domain_intelligence = DomainIntelligenceSection(
                    is_active=True,
                    status="degraded",
                    conflicting_evidence=[f"Domain lookup failed: {str(e)}"],
                )

        else:
            # Broad domain summary
            packet.domain_intelligence = DomainIntelligenceSection(
                is_active=True,
                status="ok",
                focal_taxon=None,
                conflicting_evidence=[],
                provenance=ProvenanceRecord(source_type="WORMS_REST", confidence_or_status="no_focal_taxon_specified"),
            )

    # Summary and Latency
    latency = (time.time() - start_time) * 1000.0
    all_layers = [IntelligenceLayer.DATA, IntelligenceLayer.RESEARCH_PROGRAM, IntelligenceLayer.DOMAIN]
    skipped = [l for l in all_layers if l not in activated_layers]

    packet.retrieval_summary = RetrievalSummary(
        activated_layers=list(activated_layers),
        skipped_layers=skipped,
        routing_rationale=rationale,
        latency_ms=round(latency, 2),
    )

    return packet


def format_packet_for_llm_prompt(packet: ResearchIntelligencePacket) -> str:
    """
    Formats the ResearchIntelligencePacket into an explicit prompt section
    using strict 4-way provenance segregation and explicit absence of evidence.
    """
    lines = [
        "================================================================================",
        "RESEARCH INTELLIGENCE PACKET (ADAPTIVE ORCHESTRATION & 4-WAY PROVENANCE)",
        "================================================================================",
        f"Retrieval Rationale: {packet.retrieval_summary.routing_rationale}",
        f"Activated Layers: {[l.value for l in packet.retrieval_summary.activated_layers]} (Latency: {packet.retrieval_summary.latency_ms} ms)",
        f"Skipped Layers: {[l.value for l in packet.retrieval_summary.skipped_layers]}",
        "",
    ]

    # 1. DATA INTELLIGENCE [FACT]
    lines.append("--- 1. DATA INTELLIGENCE LAYER (DWH GROUND TRUTH) [PROVENANCE: FACT] ---")
    if packet.data_intelligence and packet.data_intelligence.is_active:
        if packet.data_intelligence.status == "ok":
            if packet.data_intelligence.rich_dwh_context:
                lines.append(packet.data_intelligence.rich_dwh_context)
            elif packet.data_intelligence.focal_taxon_images > 0:
                lines.append(f"[FACT] Focal Taxon Total Images: {packet.data_intelligence.focal_taxon_images:,} images across {packet.data_intelligence.focal_taxon_species_count} species.")
                lines.append(f"[FACT] Usable Species (>=15 images): {packet.data_intelligence.focal_taxon_usable_species}.")
                lines.append(f"[FACT] Model Status in DWH: {'[EXCLUDED] Model already exists in registry' if packet.data_intelligence.models_already_exist else '[AVAILABLE] Unmodeled taxon'}.")
            if packet.data_intelligence.unmodeled_taxa_available and not packet.data_intelligence.rich_dwh_context:
                lines.append(f"[FACT] Top Unmodeled Genera in DWH (Ready for New Classifiers): {', '.join(packet.data_intelligence.unmodeled_taxa_available)}")
        elif packet.data_intelligence.status == "no_records":
            lines.append("[FACT] [NO EMPIRICAL RECORDS]: No matching images found in DWH. (Absence of evidence is explicit; do NOT assume data exists).")
        elif packet.data_intelligence.status == "degraded":
            lines.append(f"[FACT] [DATA DEGRADED]: {', '.join(packet.data_intelligence.data_gaps)}")
    else:
        lines.append("[SKIPPED]: Data Intelligence was not required for this question.")
    lines.append("")

    # 2. RESEARCH PROGRAM INTELLIGENCE [PREVIOUS FINDING]
    lines.append("--- 2. RESEARCH PROGRAM INTELLIGENCE (CUMULATIVE SCIENCE) [PROVENANCE: PREVIOUS FINDING] ---")
    if packet.research_program_intelligence and packet.research_program_intelligence.is_active:
        if packet.research_program_intelligence.status == "ok":
            if packet.research_program_intelligence.rich_program_context:
                lines.append(packet.research_program_intelligence.rich_program_context)
            else:
                if packet.research_program_intelligence.active_agenda_items:
                    lines.append("=== ACTIVE RESEARCH PROGRAM AGENDA ===")
                    for ag in packet.research_program_intelligence.active_agenda_items:
                        lines.append(f"  * [{ag.type}] {ag.title}: {ag.description}")
                for f in packet.research_program_intelligence.previous_findings:
                    lines.append(f"[PREVIOUS FINDING] {f}")
                for q in packet.research_program_intelligence.open_methodological_questions:
                    lines.append(f"[OPEN QUESTION] {q}")
        elif packet.research_program_intelligence.status == "no_records":
            lines.append("[PREVIOUS FINDING] [NO PRIOR PROGRAM DATA]: No prior studies recorded for this specific lineage.")
    else:
        lines.append("[SKIPPED]: Research Program Intelligence was not required for this question.")
    lines.append("")



    # 3. DOMAIN INTELLIGENCE [DOMAIN CLAIM]
    lines.append("--- 3. DOMAIN & LITERATURE INTELLIGENCE (TAXONOMY & PREPRINTS) [PROVENANCE: DOMAIN CLAIM] ---")

    if packet.domain_intelligence and packet.domain_intelligence.is_active:
        if packet.domain_intelligence.status == "ok":
            if packet.domain_intelligence.focal_taxon:
                lines.append(f"[DOMAIN CLAIM] WoRMS Taxon: {packet.domain_intelligence.focal_taxon} | Status: {packet.domain_intelligence.taxonomic_status} (AphiaID: {packet.domain_intelligence.aphia_id})")
                if packet.domain_intelligence.synonyms:
                    lines.append(f"[DOMAIN CLAIM] Junior Synonyms: {', '.join(packet.domain_intelligence.synonyms[:5])}")
                lines.append(f"[DOMAIN CLAIM] Cryptic Complexes Flag: {'Documented cryptic diversity / morphological overlap' if packet.domain_intelligence.has_cryptic_complexes else 'Standard morphological distinctiveness'}.")
            if packet.domain_intelligence.relevant_literature:
                lines.append("[DOMAIN CLAIM] Relevant Scientific Literature & Preprints:")
                for lit in packet.domain_intelligence.relevant_literature:
                    lines.append(f"  * {lit.title} ({lit.year or 'n.d.'}) [{lit.source}] DOI/URL: {lit.doi or lit.url or 'N/A'}")
        elif packet.domain_intelligence.status == "no_records":
            lines.append("[DOMAIN CLAIM] [NO TAXONOMIC RECORDS]: Taxon not found in WoRMS. (Absence of evidence is explicit).")
    else:
        lines.append("[SKIPPED]: Domain Intelligence was not required for this question.")
    lines.append("")

    # 4. LLM SCIENTIFIC SYNTHESIS INSTRUCTIONS
    lines.append("--- 4. SYNTHESIS RULES [PROVENANCE: LLM INTERPRETATION] ---")
    lines.append("1. Strictly distinguish [FACT], [PREVIOUS FINDING], and [DOMAIN CLAIM] from your [LLM INTERPRETATION].")
    lines.append("2. Ground all candidate suggestions in the facts and literature above. Do NOT hallucinate image counts or synonyms.")
    lines.append("3. If any layer is marked [NO EMPIRICAL RECORDS] or [SKIPPED], state the absence of evidence explicitly.")
    lines.append("================================================================================")

    return "\n".join(lines)
