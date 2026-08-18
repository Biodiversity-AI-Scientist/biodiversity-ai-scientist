from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.research_agenda import ResearchAgendaItem
from src.schemas.research_agenda import (
    ResearchAgendaItemCreate,
    ResearchAgendaItemUpdate,
)


DEFAULT_AGENDA_ITEMS = [
    {
        "title": "Cross-Genus Variation in Species Classification Difficulty",
        "description": "What biological, morphological, or data-distribution factors explain why some marine molluscan genera achieve >95% accuracy while others with equal training sample sizes plateau below 75%?",
        "type": "cross_study_hypothesis",
        "status": "investigating",
        "source_reference": "FindShell Empirical Synthesis 2024-2026",
        "current_evidence": "Conus achieves high accuracy (>92%) despite 800+ species due to strong aperture and pattern geometry; Tellinidae requires genus-first routing due to visual conservatism in bivalve outlines.",
        "known_limitations": "Existing evaluations are confounded by variable image counts per species and differing ratios of studio vs field photos.",
        "follow_up_opportunities": "Evaluate unmodeled diverse genera (such as Nassarius, Chicoreus, or Cypraea) using standardized class-balanced protocols.",
    },
    {
        "title": "Impact of Species Class Richness on Classifier Scalability",
        "description": "Does species classification difficulty scale linearly or logarithmically with species count, and where do flat CNNs fail in high-diversity clades?",
        "type": "open_question",
        "status": "open",
        "source_reference": "Identifying Shells using CNNs (Blog Dec 2024)",
        "current_evidence": "Top-1 accuracy degrades as class count exceeds 50 unless hierarchical routing or fine-grained backbone fine-tuning is employed.",
        "known_limitations": "Most single-genus studies only test between 5 and 30 species.",
        "follow_up_opportunities": "Benchmark classification accuracy across genera with varying species richness (e.g. Nassarius with 50+ represented species vs Morum with 10-15).",
    },
    {
        "title": "Hierarchical Routing vs Flat Multi-Class Architectures",
        "description": "Under which taxonomic conditions does hierarchical classification (Family -> Genus -> Species) outperform flat end-to-end classification?",
        "type": "methodological_issue",
        "status": "partially_resolved",
        "source_reference": "Epitoniidae & Tellinidae Technical Reports",
        "current_evidence": "In Tellinidae, genus-first routing improved species identification by eliminating cross-genus false positives caused by conserved shell shape.",
        "known_limitations": "Hierarchical routing introduces cascading errors if the upper-level taxonomic router errs.",
        "follow_up_opportunities": "Test hierarchical routing on gastropod families with high genus diversity (e.g. Nassariidae, Muricidae).",
    },
    {
        "title": "Leakage-Aware and Source-Aware Partitioning",
        "description": "How strongly does studio vs field imagery source bias inflate apparent accuracy, and does source-aware stratification guarantee out-of-distribution generalization?",
        "type": "methodological_issue",
        "status": "partially_resolved",
        "source_reference": "Morum Technical Report & Image Dataset Bias Blog",
        "current_evidence": "Naive random splitting across museum specimen images from identical collectors creates near-duplicate leakage. Source-aware splitting reveals true generalization bounds.",
        "known_limitations": "Requires specimen-level or collector-level source metadata, which is missing for some historical DWH image records.",
        "follow_up_opportunities": "Mandate source-aware and specimen-aware train/test splits for all new genus model benchmarks.",
    },
    {
        "title": "Conservative Statistical Label Curation on Noisy Curations",
        "description": "When does conservative statistical label auditing materially improve classifier reliability on visually noisy museum datasets?",
        "type": "methodological_issue",
        "status": "partially_resolved",
        "source_reference": "Harpa & Clathurellidae Technical Reports",
        "current_evidence": "Statistical confidence auditing and cross-fold loss filtering pruned ~4% mislabeled historical specimen records, yielding sharper confusion matrices.",
        "known_limitations": "Aggressive pruning risks eliminating rare morphotypes or valid phenotypic extremes.",
        "follow_up_opportunities": "Apply automated loss-based label auditing to unmodeled candidate datasets during preprocessing.",
    },
    {
        "title": "Few-Shot Sample Size Thresholds and Data Efficiency",
        "description": "What is the minimum per-species image threshold required for fine-tuning EfficientNet/ResNet models before few-shot failure occurs?",
        "type": "limitation",
        "status": "partially_resolved",
        "source_reference": "Minimum Images per Species & Morum Few-Shot (Harpidae)",
        "current_evidence": "Pretrained CNN backbones achieve acceptable top-1 accuracy (>80%) with as few as 15-25 high-quality images per species; below 10 images, representations collapse without synthetic augmentation.",
        "known_limitations": "Data efficiency is heavily dependent on intra-specific color and shape polymorphism.",
        "follow_up_opportunities": "Explore few-shot transfer learning on low-count species within high-count candidate genera.",
    },
    {
        "title": "Self-Supervised Vision Embeddings vs Geometric Morphometrics",
        "description": "When do self-supervised representations (e.g. DINOv3, SimCLR) extract biologically meaningful shell morphology compared to classical landmarks?",
        "type": "research_opportunity",
        "status": "investigating",
        "source_reference": "Conus pennaceus Complex & DINOv3 Harpa Reports",
        "current_evidence": "DINOv3 latent representations cluster specimens by spire angle, whorl count, and color pattern gradients without supervision, aligning closely with geometric morphometrics.",
        "known_limitations": "Self-supervised features may attend to irrelevant background artifacts if object masks are absent.",
        "follow_up_opportunities": "Extract DINOv3 feature vectors on Nassarius shell contours to quantify morphometric clusters and compare with classical taxonomic diagnoses.",
    },
    {
        "title": "Resolving Cryptic Species Complexes via Morphometric AI Triage",
        "description": "Do high visual classification errors and embedding sub-clusters correspond to recognized taxonomic controversies or cryptic species complexes?",
        "type": "cross_study_hypothesis",
        "status": "open",
        "source_reference": "Species Delimitation as Human-Led Triage (Cone Snails COX1)",
        "current_evidence": "In Conus, AI embedding clustering identified 3 cryptic sub-lineages that were subsequently confirmed by COX1 mitochondrial barcoding.",
        "known_limitations": "Morphological clustering cannot prove reproductive isolation without molecular or ecological validation.",
        "follow_up_opportunities": "Target candidate genera with documented taxonomic dispute (e.g. Nassarius, Chicoreus) to identify candidate cryptic complexes for DNA validation.",
    },
]


def create_agenda_item(
    db: Session,
    item_data: ResearchAgendaItemCreate,
) -> ResearchAgendaItem:
    item = ResearchAgendaItem(
        title=item_data.title,
        description=item_data.description,
        type=item_data.type,
        status=item_data.status,
        origin_project_id=item_data.origin_project_id,
        origin_research_plan_id=item_data.origin_research_plan_id,
        origin_result_id=item_data.origin_result_id,
        source_reference=item_data.source_reference,
        current_evidence=item_data.current_evidence,
        known_limitations=item_data.known_limitations,
        follow_up_opportunities=item_data.follow_up_opportunities,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_agenda_item(
    db: Session,
    item_id: int,
) -> ResearchAgendaItem | None:
    return db.get(ResearchAgendaItem, item_id)


def list_agenda_items(
    db: Session,
    status_filter: str | None = None,
    type_filter: str | None = None,
    limit: int = 100,
) -> list[ResearchAgendaItem]:
    query = select(ResearchAgendaItem)
    if status_filter:
        query = query.where(ResearchAgendaItem.status == status_filter)
    if type_filter:
        query = query.where(ResearchAgendaItem.type == type_filter)
    statement = query.order_by(ResearchAgendaItem.id.asc()).limit(limit)
    return list(db.scalars(statement).all())


def update_agenda_item(
    db: Session,
    item: ResearchAgendaItem,
    update_data: ResearchAgendaItemUpdate,
) -> ResearchAgendaItem:
    data = update_data.model_dump(exclude_unset=True)
    for key, val in data.items():
        setattr(item, key, val)
    db.commit()
    db.refresh(item)
    return item


def seed_default_research_agenda_if_empty(db: Session) -> int:
    existing_count = db.query(ResearchAgendaItem).count()
    if existing_count > 0:
        return 0
    added = 0
    for data in DEFAULT_AGENDA_ITEMS:
        item = ResearchAgendaItem(**data)
        db.add(item)
        added += 1
    db.commit()
    return added
