import logging
import os
import urllib.request
import urllib.parse
import json
import re
from typing import Any
from sqlalchemy.orm import Session

from src.models.research_agenda import ResearchAgendaItem
from src.repositories.research_agenda import (
    list_agenda_items,
    seed_default_research_agenda_if_empty,
)

logger = logging.getLogger(__name__)

PAPERS_API_URL = os.getenv("PAPERS_API_URL", "")
FINDSHELL_BLOG_URL = os.getenv("FINDSHELL_BLOG_URL", "")


def search_papers_api(query: str, limit: int = 5, timeout: float = 4.0) -> list[dict[str, Any]]:
    """Query the optional scientific papers REST API if configured."""
    base_url = (PAPERS_API_URL or os.getenv("PAPERS_API_URL") or "").rstrip("/")
    if not base_url:
        return []

    encoded_q = urllib.parse.quote_plus(query)
    url = f"{base_url}/api/search?q={encoded_q}&limit={limit}"
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "AI-Scientist/1.2 (Cumulative Science)", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("results", [])
    except Exception as exc:
        logger.warning("Papers API query failed for '%s': %s", query, exc)
        return []


def get_findshell_publications_index(timeout: float = 4.0) -> list[dict[str, str]]:
    """Parse the FindShell publication index if configured or return baseline bibliography."""
    blog_url = FINDSHELL_BLOG_URL or os.getenv("FINDSHELL_BLOG_URL") or ""
    if blog_url:
        try:
            req = urllib.request.Request(
                blog_url,
                headers={"User-Agent": "AI-Scientist/1.2", "Accept": "text/html"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                html = resp.read().decode("utf-8", errors="replace")
                # Extract links with blog- or ai-in-integrative-taxonomy
                pattern = re.compile(r'<a\s+(?:[^>]*?\s+)?href="([^"]*(?:blog-|ai-in-integrative)[^"]*)"[^>]*>(.*?)<\/a>', re.IGNORECASE | re.DOTALL)
                articles = []
                seen = set()
                base_domain = blog_url.rsplit("/", 1)[0]
                for href, title in pattern.findall(html):
                    clean_title = re.sub(r'<[^>]+>', '', title).strip()
                    if clean_title and clean_title not in seen:
                        seen.add(clean_title)
                        articles.append({
                            "title": clean_title,
                            "url": href if href.startswith("http") else f"{base_domain}/{href.lstrip('/')}",
                        })
                if articles:
                    return articles
        except Exception as exc:
            logger.warning("FindShell blog index fetch failed: %s", exc)

    # Fallback list of primary known publications with generic/relative endpoints
    base_prefix = "/findshell"
    return [
        {"title": "Minimum number of images needed for each species", "url": f"{base_prefix}/blog-minimum-number-of-images-needed-for-each-species.php"},
        {"title": "Fine-tuning EfficientNetV2 Models", "url": f"{base_prefix}/blog-fine-tuning-efficientnetv2-models.php"},
        {"title": "Hierarchical CNN to identify Mollusca", "url": f"{base_prefix}/blog-hierarchical-cnn-to-identify-mollusca.php"},
        {"title": "Species Delimitation as Human-Led Triage: A Stability-Aware Embedding Benchmark", "url": f"{base_prefix}/blog-species-delimitation.php"},
        {"title": "Visual Diagnosability in Tellinidae: Genus-First CNN Routing", "url": f"{base_prefix}/blog-tech-report-tellinidae.php"},
        {"title": "Source-Aware Training Improves Robustness in Leakage-Aware CNN Classification of Morum", "url": f"{base_prefix}/blog-tech-report-morum.php"},
        {"title": "Conservative Statistical Label Curation for Leakage-Aware CNN Classification of Harpa", "url": f"{base_prefix}/blog-tech-report-harpa.php"},
        {"title": "DINOv3 Improves Class-Balanced Recovery but Not Global Accuracy in Harpa", "url": f"{base_prefix}/blog-tech-report-dino.php"},
        {"title": "Phenotypic Structure in the Conus pennaceus Complex: Interpretable Morphometrics and Embeddings", "url": f"{base_prefix}/blog-pennaceus-list.php"},
    ]


def build_research_program_summary(db: Session, focal_taxa: list[str] | None = None) -> str:
    """
    Synthesizes active ResearchAgendaItems, FindShell technical findings,
    and relevant literature from the Papers API into a structured string for the LLM.
    """
    seed_default_research_agenda_if_empty(db)
    agenda_items = list_agenda_items(db, limit=20)
    
    sections = []
    
    # 1. Active Research Agenda (Core Program Questions)
    agenda_lines = ["ACTIVE RESEARCH PROGRAM AGENDA (OPEN & METHODOLOGICAL ISSUES):"]
    for item in agenda_items:
        agenda_lines.append(
            f"- [{item.status.upper()} | {item.type}] {item.title}\n"
            f"  Description: {item.description}\n"
            f"  Current Evidence: {item.current_evidence or 'N/A'}\n"
            f"  Follow-up Opportunity: {item.follow_up_opportunities or 'N/A'}"
        )
    sections.append("\n".join(agenda_lines))
    
    # 2. FindShell Key Technical Takeaways
    findshell_summary = (
        "CORE METHODOLOGICAL FINDINGS FROM FINDSHELL RESEARCH PROGRAM:\n"
        "- Classification Difficulty vs Class Richness: Flat CNN accuracy drops in clades with >50 classes; hierarchical genus/family routing avoids conserved-shape errors.\n"
        "- Leakage-Aware & Source-Aware Splitting: Random splits across museum collections overestimate accuracy; source-aware stratification is required.\n"
        "- Label Curation: Statistical loss auditing cleans ~4-5% legacy misidentifications without discarding polymorphic variants.\n"
        "- Vision Embeddings: DINOv3 self-supervised embeddings detect morphological clusters (spire angle, whorls) congruent with geometric morphometrics.\n"
        "- Cryptic Complexes: High classifier confusion paired with embedding sub-clustering reliably flags candidate cryptic species complexes for integrative taxonomy (e.g. COX1 validation)."
    )
    sections.append(findshell_summary)
    
    # 3. Targeted Literature Search if focal taxa provided
    if focal_taxa:
        lit_lines = ["RELEVANT RESEARCH PROGRAM LITERATURE & CITATIONS:"]
        for taxon in focal_taxa[:3]:
            results = search_papers_api(taxon, limit=2)
            for p in results:
                authors = p.get("authors") or "Unknown"
                year = p.get("year") or "N/D"
                title = p.get("title") or "Untitled"
                lit_lines.append(f"- ({year}) {title} by {authors} [ID: {p.get('paper_id')}]")
        if len(lit_lines) > 1:
            sections.append("\n".join(lit_lines))
            
    return "\n\n".join(sections)
