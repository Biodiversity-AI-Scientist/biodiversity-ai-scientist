import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.database import get_db, get_dwh_db
from src.schemas.domain_intelligence import (
    LiteratureItem,
    TaxonBiologicalContext,
    TaxonPriorityComparison,
)
from src.services.data_intelligence import get_taxon_image_summary
from src.services.domain_intelligence import (
    get_taxon_domain_intelligence,
    search_arxiv_literature,
    search_biorxiv_literature,
    search_local_papers_library,
)



logger = logging.getLogger(__name__)

router = APIRouter(prefix="/taxa", tags=["domain_intelligence"])


class CompareTaxaRequest(BaseModel):
    taxon_a: str
    taxon_b: str
    project_id: int | None = None


@router.get("/{name}/biological-context", response_model=TaxonBiologicalContext)
def get_taxon_biological_context(name: str) -> TaxonBiologicalContext:
    """
    Returns domain, WoRMS taxonomic hierarchy, and literature intelligence for a taxon.
    """
    clean_name = name.strip()
    if not clean_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Taxon name cannot be empty",
        )
    return get_taxon_domain_intelligence(clean_name)


@router.get("/{name}/literature", response_model=list[LiteratureItem])
def get_taxon_literature(
    name: str,
    max_results: int = Query(default=5, ge=1, le=20),
) -> list[LiteratureItem]:
    """
    Searches both preprint archives (arXiv/bioRxiv) and the local scientific paper library.
    """
    clean_name = name.strip()
    if not clean_name:
        return []

    items: list[LiteratureItem] = []
    items.extend(search_biorxiv_literature(clean_name, max_results=max_results))
    items.extend(search_arxiv_literature(clean_name, max_results=max_results))
    items.extend(search_local_papers_library(clean_name, max_results=max_results))
    return items



@router.post("/compare-priorities", response_model=TaxonPriorityComparison)
def compare_taxa_priorities(
    req: CompareTaxaRequest,
    dwh_db: Session | None = Depends(get_dwh_db),
    db: Session = Depends(get_db),
) -> TaxonPriorityComparison:
    """
    Compares two candidate genera across Data Intelligence, Research Program Value,
    and Domain/Taxonomic Importance to recommend scientific prioritization.
    """
    taxon_a = req.taxon_a.strip().capitalize()
    taxon_b = req.taxon_b.strip().capitalize()

    # 1. Data Intelligence (DWH)
    dwh_a: dict[str, Any] = {"total_images": 0, "distinct_species_count": 0, "status": "no_dwh"}
    dwh_b: dict[str, Any] = {"total_images": 0, "distinct_species_count": 0, "status": "no_dwh"}
    if dwh_db:
        try:
            dwh_a = get_taxon_image_summary(dwh_db, taxon_a).model_dump()
            dwh_b = get_taxon_image_summary(dwh_db, taxon_b).model_dump()
        except Exception as e:
            logger.warning("DWH query in comparison failed: %s", e)


    # 2. Domain Intelligence (WoRMS + Preprints)
    domain_a = get_taxon_domain_intelligence(taxon_a)
    domain_b = get_taxon_domain_intelligence(taxon_b)

    # 3. Scientific Prioritization Reasoning
    score_a = 0
    score_b = 0

    # Data Feasibility weight
    imgs_a = dwh_a.get("total_images", 0)
    imgs_b = dwh_b.get("total_images", 0)
    if imgs_a >= 1000: score_a += 2
    elif imgs_a >= 100: score_a += 1
    if imgs_b >= 1000: score_b += 2
    elif imgs_b >= 100: score_b += 1

    # Domain Importance weight (Cryptic complexes, morphological challenges, taxonomic controversies)
    bio_relevance_a = len(domain_a.morphological_challenges) + len(domain_a.unresolved_knowledge_gaps) + (2 if domain_a.has_cryptic_complexes else 0)
    bio_relevance_b = len(domain_b.morphological_challenges) + len(domain_b.unresolved_knowledge_gaps) + (2 if domain_b.has_cryptic_complexes else 0)

    score_a += bio_relevance_a
    score_b += bio_relevance_b

    if score_b > score_a and imgs_b >= 50:
        winner = taxon_b
        justification = (
            f"While {taxon_a} has verified data coverage ({imgs_a} images), {taxon_b} combines sufficient data feasibility "
            f"({imgs_b} images) with substantially greater biological/taxonomic importance: "
            f"it presents documented cryptic complexes ({'yes' if domain_b.has_cryptic_complexes else 'no'}), "
            f"{len(domain_b.morphological_challenges)} documented morphological convergence challenges, and unresolved species boundaries."
        )
    elif score_a > score_b and imgs_a >= 50:
        winner = taxon_a
        justification = (
            f"{taxon_a} is prioritized over {taxon_b} because it combines strong data feasibility ({imgs_a} images) "
            f"with higher taxonomic/morphological relevance and critical knowledge gaps ({len(domain_a.unresolved_knowledge_gaps)} identified gaps)."
        )
    else:
        winner = taxon_a if imgs_a >= imgs_b else taxon_b
        justification = f"Both taxa show comparable biological importance; {winner} has higher image density in DWH."

    return TaxonPriorityComparison(
        taxon_a=taxon_a,
        taxon_b=taxon_b,
        taxon_a_summary={
            "data_feasibility": dwh_a,
            "domain_context": domain_a.model_dump(),
        },
        taxon_b_summary={
            "data_feasibility": dwh_b,
            "domain_context": domain_b.model_dump(),
        },
        recommended_priority=winner,
        justification=justification,
        comparative_dimensions={
            "data_feasibility": {taxon_a: imgs_a, taxon_b: imgs_b},
            "biological_challenges": {taxon_a: bio_relevance_a, taxon_b: bio_relevance_b},
            "cryptic_complexes": {taxon_a: domain_a.has_cryptic_complexes, taxon_b: domain_b.has_cryptic_complexes},
        },
    )
