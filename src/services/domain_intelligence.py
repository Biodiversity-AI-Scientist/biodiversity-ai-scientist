import logging
import os
import xml.etree.ElementTree as ET
from typing import Any
import httpx

from src.schemas.domain_intelligence import (
    LiteratureItem,
    TaxonBiologicalContext,
    WormsTaxonomicRecord,
)

logger = logging.getLogger(__name__)

# Simple in-memory cache to avoid redundant network round-trips during brainstorming
_DOMAIN_CACHE: dict[str, Any] = {}


def fetch_worms_record(taxon_name: str, timeout: float = 6.0) -> WormsTaxonomicRecord | None:
    """
    Fetches official taxonomic status and hierarchy from World Register of Marine Species (WoRMS) REST API.
    """
    clean_name = taxon_name.strip()
    cache_key = f"worms_{clean_name.lower()}"
    if cache_key in _DOMAIN_CACHE:
        return _DOMAIN_CACHE[cache_key]

    url = f"https://www.marinespecies.org/rest/AphiaRecordsByName/{clean_name}"
    params = {"like": "false", "marine_only": "true"}

    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(url, params=params)
            if resp.status_code == 200:
                records = resp.json()
                if isinstance(records, list) and len(records) > 0:
                    r = records[0]
                    aphia_id = r.get("AphiaID")
                    
                    # Fetch synonyms if available
                    synonyms: list[str] = []
                    if aphia_id:
                        try:
                            syn_resp = client.get(f"https://www.marinespecies.org/rest/AphiaSynonymsByAphiaID/{aphia_id}")
                            if syn_resp.status_code == 200:
                                syn_data = syn_resp.json()
                                if isinstance(syn_data, list):
                                    synonyms = [s.get("scientificname") for s in syn_data if s.get("scientificname")][:10]
                        except Exception as syn_exc:
                            logger.debug("Failed to fetch WoRMS synonyms: %s", syn_exc)

                    record = WormsTaxonomicRecord(
                        aphia_id=aphia_id,
                        scientific_name=r.get("scientificname", clean_name),
                        authority=r.get("authority"),
                        rank=r.get("rank"),
                        status=r.get("status", "unknown").lower(),
                        valid_aphia_id=r.get("valid_AphiaID"),
                        valid_name=r.get("valid_name"),
                        valid_authority=r.get("valid_authority"),
                        kingdom=r.get("kingdom"),
                        phylum=r.get("phylum"),
                        class_name=r.get("class"),
                        order=r.get("order"),
                        family=r.get("family"),
                        genus=r.get("genus"),
                        is_marine=bool(r.get("isMarine")),
                        synonyms=synonyms,
                        url=f"https://www.marinespecies.org/aphia.php?p=taxdetails&id={aphia_id}" if aphia_id else None,
                    )
                    _DOMAIN_CACHE[cache_key] = record
                    return record
    except Exception as exc:
        logger.warning("WoRMS API lookup failed for '%s': %s", clean_name, exc)

    return None


def search_arxiv_literature(query: str, max_results: int = 3, timeout: float = 6.0) -> list[LiteratureItem]:
    """
    Queries arXiv API for preprints related to computer vision, biodiversity, or deep learning.
    """
    clean_query = query.strip()
    cache_key = f"arxiv_{clean_query.lower()}_{max_results}"
    if cache_key in _DOMAIN_CACHE:
        return _DOMAIN_CACHE[cache_key]

    url = "https://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{clean_query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }

    items: list[LiteratureItem] = []
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(url, params=params)
            if resp.status_code == 200:
                root = ET.fromstring(resp.text)
                ns = {"atom": "http://www.w3.org/2005/Atom"}
                for entry in root.findall("atom:entry", ns):
                    title_elem = entry.find("atom:title", ns)
                    summary_elem = entry.find("atom:summary", ns)
                    published_elem = entry.find("atom:published", ns)
                    id_elem = entry.find("atom:id", ns)

                    authors: list[str] = []
                    for author in entry.findall("atom:author", ns):
                        name_elem = author.find("atom:name", ns)
                        if name_elem is not None and name_elem.text:
                            authors.append(name_elem.text.strip())

                    title = title_elem.text.strip().replace("\n", " ") if title_elem is not None and title_elem.text else "Untitled"
                    abstract = summary_elem.text.strip().replace("\n", " ") if summary_elem is not None and summary_elem.text else None
                    year = None
                    if published_elem is not None and published_elem.text and len(published_elem.text) >= 4:
                        try:
                            year = int(published_elem.text[:4])
                        except ValueError:
                            pass
                    arxiv_url = id_elem.text.strip() if id_elem is not None and id_elem.text else None

                    items.append(LiteratureItem(
                        title=title,
                        authors=authors[:4],
                        year=year,
                        source="arXiv (Computer Vision & Biology)",
                        url=arxiv_url,
                        abstract=abstract[:300] + "..." if abstract and len(abstract) > 300 else abstract,
                    ))
                _DOMAIN_CACHE[cache_key] = items
                return items
    except Exception as exc:
        logger.warning("arXiv lookup failed for '%s': %s", clean_query, exc)

    return []


def search_biorxiv_literature(query: str, max_results: int = 3, timeout: float = 6.0) -> list[LiteratureItem]:
    """
    Queries bioRxiv preprints for biology, phylogenetics, and biodiversity studies.
    """
    clean_query = query.strip()
    cache_key = f"biorxiv_{clean_query.lower()}_{max_results}"
    if cache_key in _DOMAIN_CACHE:
        return _DOMAIN_CACHE[cache_key]

    headers = {"User-Agent": "BiodiversityAIScientist/1.0 (mailto:ai-scientist@local.lab)"}
    url = "https://api.crossref.org/works"
    params = {
        "query": clean_query,
        "filter": "prefix:10.1101",
        "rows": max_results,
    }

    items: list[LiteratureItem] = []
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                raw_items = resp.json().get("message", {}).get("items", [])
                for it in raw_items:
                    titles = it.get("title", [])
                    title = titles[0] if titles else "bioRxiv Preprint"
                    doi = it.get("DOI")
                    
                    authors: list[str] = []
                    for a in it.get("author", []):
                        family = a.get("family", "")
                        given = a.get("given", "")
                        name = f"{given} {family}".strip() or family
                        if name:
                            authors.append(name)
                    
                    year = None
                    created_parts = it.get("created", {}).get("date-parts", [[]])
                    if created_parts and len(created_parts[0]) > 0 and created_parts[0][0]:
                        year = int(created_parts[0][0])
                    
                    url_val = f"https://doi.org/{doi}" if doi else None
                    items.append(LiteratureItem(
                        title=title,
                        authors=authors[:4],
                        year=year,
                        source="bioRxiv (Biology & Biodiversity)",
                        doi=doi,
                        url=url_val,
                    ))
                _DOMAIN_CACHE[cache_key] = items
                return items
    except Exception as exc:
        logger.warning("bioRxiv preprint lookup failed for '%s': %s", clean_query, exc)

    return []


def search_local_papers_library(query: str, max_results: int = 3, timeout: float = 4.0) -> list[LiteratureItem]:
    """
    Searches scientific literature indexed on the optional Papers API if configured.
    """
    clean_query = query.strip()
    cache_key = f"local_papers_{clean_query.lower()}_{max_results}"
    if cache_key in _DOMAIN_CACHE:
        return _DOMAIN_CACHE[cache_key]

    papers_api_url = (os.getenv("PAPERS_API_URL") or "").rstrip("/")
    if not papers_api_url:
        return []

    url = f"{papers_api_url}/api/search"
    params = {"q": clean_query, "limit": max_results, "mode": "or"}

    items: list[LiteratureItem] = []
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results") or []
                for r in results:
                    items.append(LiteratureItem(
                        title=r.get("title") or r.get("filename") or "Scientific Paper",
                        authors=[r.get("authors")] if r.get("authors") else [],
                        year=r.get("year"),
                        source="Domain Scientific Papers Index",
                        doi=r.get("doi"),
                        url=r.get("url"),
                        relevance_note=f"Collection: {r.get('collection') or 'General'}",
                    ))
                _DOMAIN_CACHE[cache_key] = items
                return items
    except Exception as exc:
        logger.debug("Local papers search skipped or failed: %s", exc)

    return []


def get_taxon_domain_intelligence(taxon_name: str) -> TaxonBiologicalContext:
    """
    Synthesizes domain, taxonomic, and literature intelligence for a focal taxon.
    """
    worms_rec = fetch_worms_record(taxon_name)
    
    # Gather literature from bioRxiv (biology), arXiv (vision), and local library
    literature: list[LiteratureItem] = []
    
    lit_biorxiv = search_biorxiv_literature(taxon_name, max_results=2)
    literature.extend(lit_biorxiv)

    lit_arxiv = search_arxiv_literature(f"{taxon_name} classification OR {taxon_name} species", max_results=2)
    literature.extend(lit_arxiv)

    lit_local = search_local_papers_library(taxon_name, max_results=2)
    literature.extend(lit_local)


    # Determine stability & known domain challenges
    taxonomic_stability = "stable"
    has_cryptic_complexes = False
    morphological_challenges: list[str] = []
    unresolved_gaps: list[str] = []

    if worms_rec:
        if worms_rec.status in ("unaccepted", "synonym"):
            taxonomic_stability = "complex_synonymy"
            unresolved_gaps.append(f"Taxon is currently considered {worms_rec.status}; accepted valid name is '{worms_rec.valid_name}'.")
        elif len(worms_rec.synonyms) >= 3:
            taxonomic_stability = "controversial"
            unresolved_gaps.append(f"High synonymy count ({len(worms_rec.synonyms)} junior synonyms), indicating historical taxonomic flux.")

    # Domain heuristics for well-studied marine gastropod clades
    lower_name = taxon_name.lower()
    if lower_name in ("nassarius", "nassariidae"):
        has_cryptic_complexes = True
        morphological_challenges.append("High intraspecific shell color polymorphism and axial ribbing variation")
        morphological_challenges.append("Cryptic sibling species complexes requiring aperture landmarking")
        unresolved_gaps.append("Discordance between conchological morphotypes and COI/28S molecular phylogenies in Indo-Pacific clades")
    elif lower_name in ("vexillum", "costellariidae"):
        has_cryptic_complexes = True
        morphological_challenges.append("Extremely high morphological convergence in spire elongation and spiral cord patterns")
        unresolved_gaps.append("Subgeneric boundaries poorly resolved; recent molecular revisions splitting historical morphological subgenera")
    elif lower_name in ("mitra", "mitridae"):
        morphological_challenges.append("Smooth shell surfaces lack discrete suture landmarks; classification relies on columellar plicae")
        unresolved_gaps.append("Radular vs conchological classification mismatches in tropical reef taxa")

    return TaxonBiologicalContext(
        taxon_name=taxon_name,
        worms=worms_rec,
        taxonomic_stability=taxonomic_stability,
        has_cryptic_complexes=has_cryptic_complexes,
        morphological_challenges=morphological_challenges,
        literature_citations=literature,
        unresolved_knowledge_gaps=unresolved_gaps,
    )


def format_domain_intelligence_for_prompt(context: TaxonBiologicalContext) -> str:
    """
    Formats the domain and literature context for injection into LLM brainstorming prompts.
    """
    lines: list[str] = [f"### Domain & Literature Intelligence for '{context.taxon_name}':"]

    if context.worms:
        w = context.worms
        lines.append(f"- **WoRMS Status**: {w.status.upper()} (AphiaID: {w.aphia_id or 'N/A'})")
        if w.status != "accepted" and w.valid_name:
            lines.append(f"  - Valid Name: *{w.valid_name}* ({w.valid_authority or 'N/A'})")
        if w.family:
            lines.append(f"  - Family: {w.family} | Order: {w.order or 'N/A'}")
        if w.synonyms:
            lines.append(f"  - Synonyms / Historical Names: {', '.join(w.synonyms[:5])}")
    else:
        lines.append("- **WoRMS Status**: No direct marine species record found (or external API degraded).")

    lines.append(f"- **Taxonomic Stability**: {context.taxonomic_stability.replace('_', ' ').title()}")
    if context.has_cryptic_complexes:
        lines.append("- **Cryptic Diversity / Complexes**: Documented cryptic species boundaries and high intraspecific variability.")

    if context.morphological_challenges:
        lines.append("- **Known Morphological Identification Challenges**:")
        for mc in context.morphological_challenges:
            lines.append(f"  * {mc}")

    if context.unresolved_knowledge_gaps:
        lines.append("- **Scientific Knowledge Gaps & Controversies**:")
        for gap in context.unresolved_knowledge_gaps:
            lines.append(f"  * {gap}")

    if context.literature_citations:
        lines.append("- **Identifiable Literature & Preprint References**:")
        for lit in context.literature_citations[:4]:
            author_str = f"{lit.authors[0]} et al." if lit.authors else "Authors unspecified"
            year_str = f" ({lit.year})" if lit.year else ""
            lines.append(f"  * [{lit.source}] {author_str}{year_str}: \"{lit.title}\"")
            if lit.url:
                lines.append(f"    Link: {lit.url}")

    return "\n".join(lines)
