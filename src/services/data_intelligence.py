import logging
from typing import Any
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.schemas.data_intelligence import (
    DatasetClassDistribution,
    DatasetVersionSummary,
    FeasibilityEvaluationRequest,
    FeasibilityEvaluationResponse,
    GenusImageCountSummary,
    ModelNetworkSummary,
    ModelPerformanceSummary,
    SourceSummaryItem,
    SpeciesImageCount,
    TaxonImageSummary,
)

logger = logging.getLogger(__name__)


def get_existing_model_networks(
    db: Session,
    taxon_name: str | None = None,
    taxon_level: str | None = None,
) -> list[ModelNetworkSummary]:
    """Queries DWH.ModelNetwork for active/deployed neural network models."""
    try:
        clauses = []
        params = {}
        if taxon_name and taxon_name.strip():
            clauses.append("(Taxon = :taxon OR model LIKE :taxon_like)")
            params["taxon"] = taxon_name.strip()
            params["taxon_like"] = f"%{taxon_name.strip()}%"
        if taxon_level and taxon_level.strip():
            clauses.append("TaxonLevel = :taxon_level")
            params["taxon_level"] = taxon_level.strip().upper()

        where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = text(
            f"""
            SELECT Taxon, TaxonLevel, TaxonLevelResult, ViewType, model, IsDefault, CreateDatetime
            FROM ModelNetwork
            {where_clause}
            ORDER BY Taxon ASC, ViewType ASC
            """
        )
        rows = db.execute(sql, params).fetchall()
        return [
            ModelNetworkSummary(
                taxon_name=r[0] or "",
                taxon_level=r[1],
                taxon_level_result=r[2],
                view_type=r[3],
                model_path=r[4],
                is_default=bool(r[5] if r[5] is not None else 1),
                created_at=r[6],
            )
            for r in rows
        ]
    except Exception as exc:
        logger.debug("get_existing_model_networks query failed: %s", exc)
        return []


def get_top_unmodeled_genera(
    db: Session,
    marine_only: bool = False,
    class_name: str | None = None,
    limit: int = 15,
) -> list[dict[str, Any]]:
    """Returns top unmodeled genera with high image counts from TaxonClass that do not yet have models in ModelNetwork."""
    try:
        clauses = ["tc.TaxonType = 'Genus'", "tc.NoImages > 100", "mn.ID IS NULL"]
        params: dict[str, Any] = {"limit": limit}
        if marine_only:
            clauses.append("tc.Marine = 1")
        if class_name:
            clauses.append("tc.ClassName = :class_name")
            params["class_name"] = class_name.strip()

        where_clause = " AND ".join(clauses)
        sql = text(
            f"""
            SELECT tc.TaxonName, tc.Family, tc.ClassName, tc.NoImages, tc.NoTransform
            FROM TaxonClass tc
            LEFT JOIN ModelNetwork mn ON mn.Taxon = tc.TaxonName
            WHERE {where_clause}
            ORDER BY tc.NoImages DESC
            LIMIT :limit
            """
        )
        rows = db.execute(sql, params).fetchall()
        return [
            {
                "genus_name": r[0],
                "family_name": r[1],
                "class_name": r[2],
                "total_images": int(r[3] or 0),
                "transformed_images": int(r[4] or 0),
            }
            for r in rows
        ]
    except Exception as exc:
        logger.debug("get_top_unmodeled_genera failed: %s", exc)
        return []



def get_taxon_image_summary(
    db: Session,
    taxon_name: str,
    rank: str | None = None,
) -> TaxonImageSummary:
    """Aggregates total image count, distinct species, views, source distribution, and existing trained models for a taxon."""
    clean_taxon = taxon_name.strip()
    if not clean_taxon:
        return TaxonImageSummary(taxon_name=taxon_name)

    detected_rank = rank
    habitat_flags: dict[str, bool] = {}

    try:
        rank_query = text(
            """
            SELECT TaxonType, Family, OrderName, ClassName, Land, Freshwater, Brackish, Marine, OnlyFossil
            FROM TaxonClass
            WHERE TaxonName = :taxon
            LIMIT 1
            """
        )
        rank_row = db.execute(rank_query, {"taxon": clean_taxon}).fetchone()
        if rank_row:
            detected_rank = rank or rank_row[0]
            habitat_flags = {
                "marine": bool(rank_row[7]),
                "land": bool(rank_row[4]),
                "freshwater": bool(rank_row[5]),
                "brackish": bool(rank_row[6]),
                "only_fossil": bool(rank_row[8]),
            }
    except Exception as exc:
        logger.debug("TaxonClass lookup skipped: %s", exc)

    rows = []
    try:
        if detected_rank and detected_rank.lower() == "family":
            sql = text(
                """
                SELECT s.SpeciesHash, s.SpeciesGenus, s.SpeciesName, s.WORMSStatus, COUNT(DISTINCT si.ImageHash) as img_count
                FROM Species s
                JOIN TaxonClass tc ON tc.TaxonName = s.SpeciesGenus AND tc.TaxonType = 'Genus'
                LEFT JOIN ShellImages si ON si.SpeciesHash = s.SpeciesHash
                WHERE tc.Family = :taxon OR tc.TaxonParent = :taxon
                GROUP BY s.SpeciesHash, s.SpeciesGenus, s.SpeciesName, s.WORMSStatus
                """
            )
        elif detected_rank and detected_rank.lower() in ("order", "ordername"):
            sql = text(
                """
                SELECT s.SpeciesHash, s.SpeciesGenus, s.SpeciesName, s.WORMSStatus, COUNT(DISTINCT si.ImageHash) as img_count
                FROM Species s
                JOIN TaxonClass tc ON tc.TaxonName = s.SpeciesGenus AND tc.TaxonType = 'Genus'
                LEFT JOIN ShellImages si ON si.SpeciesHash = s.SpeciesHash
                WHERE tc.OrderName = :taxon
                GROUP BY s.SpeciesHash, s.SpeciesGenus, s.SpeciesName, s.WORMSStatus
                """
            )
        elif detected_rank and detected_rank.lower() in ("class", "classname"):
            sql = text(
                """
                SELECT s.SpeciesHash, s.SpeciesGenus, s.SpeciesName, s.WORMSStatus, COUNT(DISTINCT si.ImageHash) as img_count
                FROM Species s
                JOIN TaxonClass tc ON tc.TaxonName = s.SpeciesGenus AND tc.TaxonType = 'Genus'
                LEFT JOIN ShellImages si ON si.SpeciesHash = s.SpeciesHash
                WHERE tc.ClassName = :taxon
                GROUP BY s.SpeciesHash, s.SpeciesGenus, s.SpeciesName, s.WORMSStatus
                """
            )
        else:
            # Default: treat as Genus
            sql = text(
                """
                SELECT s.SpeciesHash, s.SpeciesGenus, s.SpeciesName, s.WORMSStatus, COUNT(DISTINCT si.ImageHash) as img_count
                FROM Species s
                LEFT JOIN ShellImages si ON si.SpeciesHash = s.SpeciesHash
                WHERE s.SpeciesGenus = :taxon
                GROUP BY s.SpeciesHash, s.SpeciesGenus, s.SpeciesName, s.WORMSStatus
                """
            )
        rows = db.execute(sql, {"taxon": clean_taxon}).fetchall()
    except Exception as exc:
        logger.debug("Species/Images count query skipped: %s", exc)

    total_species = len(rows)
    total_images = sum(int(r[4] or 0) for r in rows)
    species_with_images = sum(1 for r in rows if int(r[4] or 0) > 0)

    worms_status_dist: dict[str, int] = {}
    for r in rows:
        st = r[3] or "unknown"
        worms_status_dist[st] = worms_status_dist.get(st, 0) + 1

    # View distribution from ImageTransform
    view_distribution = {}
    try:
        view_sql = text(
            """
            SELECT it.Viewpoint, COUNT(DISTINCT it.ID)
            FROM ImageTransform it
            JOIN Species s ON s.SpeciesHash = it.SpeciesHash
            WHERE s.SpeciesGenus = :taxon AND it.Viewpoint IS NOT NULL AND it.Viewpoint != ''
            GROUP BY it.Viewpoint
            """
        )
        view_rows = db.execute(view_sql, {"taxon": clean_taxon}).fetchall()
        view_distribution = {vr[0]: int(vr[1]) for vr in view_rows}
    except Exception:
        view_distribution = {}

    # Source distribution from ShellRecord
    source_distribution = {}
    try:
        source_sql = text(
            """
            SELECT sr.Source, COUNT(DISTINCT sr.ShellHash)
            FROM Species s
            JOIN ShellRecord sr ON sr.SpeciesHash = s.SpeciesHash
            WHERE s.SpeciesGenus = :taxon AND sr.Source IS NOT NULL
            GROUP BY sr.Source
            """
        )
        source_rows = db.execute(source_sql, {"taxon": clean_taxon}).fetchall()
        source_distribution = {sr[0]: int(sr[1]) for sr in source_rows}
    except Exception:
        source_distribution = {}

    # Query ModelNetwork for any existing models for this taxon
    existing_models = get_existing_model_networks(db, taxon_name=clean_taxon)

    return TaxonImageSummary(
        taxon_name=clean_taxon,
        rank=detected_rank or "Genus",
        total_images=total_images,
        total_species=total_species,
        species_with_images=species_with_images,
        view_distribution=view_distribution,
        source_distribution=source_distribution,
        habitat_flags=habitat_flags,
        worms_status_distribution=worms_status_dist,
        existing_models=existing_models,
    )


def get_species_image_counts(
    db: Session,
    genus_name: str,
    min_images: int = 1,
) -> list[SpeciesImageCount]:
    """Returns exact image counts and transform statistics per species in a genus."""
    clean_genus = genus_name.strip()
    if not clean_genus:
        return []

    try:
        sql = text(
            """
            SELECT 
                s.SpeciesName,
                s.SpeciesGenus,
                s.AphiaId,
                s.WORMSStatus,
                COUNT(DISTINCT si.ImageHash) as total_imgs,
                COUNT(DISTINCT it.ID) as transformed_imgs,
                GROUP_CONCAT(DISTINCT it.Viewpoint) as views_str
            FROM Species s
            LEFT JOIN ShellImages si ON si.SpeciesHash = s.SpeciesHash
            LEFT JOIN ImageTransform it ON it.SpeciesHash = s.SpeciesHash AND it.Excluded != 'Y'
            WHERE s.SpeciesGenus = :genus
            GROUP BY s.SpeciesHash, s.SpeciesName, s.SpeciesGenus, s.AphiaId, s.WORMSStatus
            ORDER BY total_imgs DESC, s.SpeciesName ASC
            """
        )
        rows = db.execute(sql, {"genus": clean_genus}).fetchall()
    except Exception as exc:
        logger.debug("get_species_image_counts query failed: %s", exc)
        return []

    results: list[SpeciesImageCount] = []
    for r in rows:
        views = [v.strip() for v in (r[6] or "").split(",") if v.strip()]
        total_imgs = int(r[4] or 0)
        transformed_imgs = int(r[5] or 0)
        meets_threshold = total_imgs >= min_images

        results.append(
            SpeciesImageCount(
                species_name=r[0],
                genus_name=r[1],
                aphia_id=r[2],
                worms_status=r[3],
                total_images=total_imgs,
                transformed_images=transformed_imgs,
                views=views,
                meets_threshold=meets_threshold,
            )
        )

    return results


def get_genus_image_counts(
    db: Session,
    family_name: str | None = None,
    order_name: str | None = None,
    class_name: str | None = None,
    min_species: int = 1,
    min_images_per_species: int = 5,
) -> list[GenusImageCountSummary]:
    """Calculates genus-level feasibility, species counts, class imbalance metrics, and cross-references existing trained models in DWH.ModelNetwork."""
    try:
        where_parts = ["tc.TaxonType = 'Genus'"]
        params = {}

        if family_name and family_name.strip():
            where_parts.append("(tc.Family = :family OR tc.TaxonParent = :family)")
            params["family"] = family_name.strip()
        if order_name and order_name.strip():
            where_parts.append("tc.OrderName = :order")
            params["order"] = order_name.strip()
        if class_name and class_name.strip():
            where_parts.append("tc.ClassName = :class")
            params["class"] = class_name.strip()

        where_clause = " AND ".join(where_parts)
        sql = text(
            f"""
            SELECT 
                tc.TaxonName as genus,
                tc.Family,
                tc.OrderName,
                tc.ClassName,
                s.SpeciesName,
                COUNT(DISTINCT si.ImageHash) as img_count
            FROM TaxonClass tc
            JOIN Species s ON s.SpeciesGenus = tc.TaxonName
            LEFT JOIN ShellImages si ON si.SpeciesHash = s.SpeciesHash
            WHERE {where_clause}
            GROUP BY tc.TaxonName, tc.Family, tc.OrderName, tc.ClassName, s.SpeciesName
            """
        )
        rows = db.execute(sql, params).fetchall()
    except Exception as exc:
        logger.debug("get_genus_image_counts query failed: %s", exc)
        return []

    # Map genus -> family/order/class and species image counts
    genus_map: dict[str, dict[str, Any]] = {}
    for r in rows:
        genus = r[0]
        if not genus:
            continue
        if genus not in genus_map:
            genus_map[genus] = {
                "family": r[1],
                "order": r[2],
                "class": r[3],
                "species_counts": {},
            }
        spec_name = r[4]
        img_cnt = int(r[5] or 0)
        genus_map[genus]["species_counts"][spec_name] = img_cnt

    # Fetch all registered models from ModelNetwork in batch
    model_networks = get_existing_model_networks(db)
    models_by_genus: dict[str, list[ModelNetworkSummary]] = {}
    for mn in model_networks:
        g_key = mn.taxon_name.strip()
        if g_key not in models_by_genus:
            models_by_genus[g_key] = []
        models_by_genus[g_key].append(mn)

    results: list[GenusImageCountSummary] = []

    for genus, data in genus_map.items():
        spec_counts = data["species_counts"]
        total_spec = len(spec_counts)
        counts_list = list(spec_counts.values())
        above_threshold = [c for c in counts_list if c >= min_images_per_species]
        total_imgs = sum(counts_list)

        if total_spec < min_species:
            continue

        min_img = min(counts_list) if counts_list else 0
        max_img = max(counts_list) if counts_list else 0
        avg_img = round(total_imgs / total_spec, 2) if total_spec > 0 else 0.0

        imbalance_ratio = round(max_img / max(min_img, 1), 2)
        is_feasible = (len(above_threshold) >= min_species) and (total_imgs >= (min_species * min_images_per_species))

        # Check existing model presence in ModelNetwork
        existing_net_models = models_by_genus.get(genus, [])
        has_existing = len(existing_net_models) > 0
        model_views = list(dict.fromkeys(m.view_type for m in existing_net_models if m.view_type))
        model_names = [m.model_path for m in existing_net_models if m.model_path]

        results.append(
            GenusImageCountSummary(
                genus_name=genus,
                family_name=data["family"],
                order_name=data["order"],
                class_name=data["class"],
                total_species=total_spec,
                species_above_threshold=len(above_threshold),
                total_images=total_imgs,
                min_images_per_species=min_img,
                max_images_per_species=max_img,
                avg_images_per_species=avg_img,
                imbalance_ratio=imbalance_ratio,
                is_feasible_for_classifier=is_feasible,
                has_existing_model=has_existing,
                existing_model_views=model_views,
                existing_models=model_names,
            )
        )

    results.sort(key=lambda g: (g.species_above_threshold, g.total_images), reverse=True)
    return results


def get_dataset_class_distribution(
    db: Session,
    dataset_name: str,
) -> DatasetClassDistribution:
    """Retrieves class distribution and sample count metrics for an existing dataset."""
    clean_ds = dataset_name.strip()
    try:
        sql = text(
            """
            SELECT it.category, COUNT(DISTINCT it.ID) as cnt, id.Genus
            FROM ImageDatasets id
            JOIN ImageTransform it ON it.ID = id.TransformID
            WHERE id.Dataset = :dataset
            GROUP BY it.category, id.Genus
            """
        )
        rows = db.execute(sql, {"dataset": clean_ds}).fetchall()
    except Exception as exc:
        logger.debug("get_dataset_class_distribution failed: %s", exc)
        return DatasetClassDistribution(dataset_name=clean_ds)

    if not rows:
        return DatasetClassDistribution(dataset_name=clean_ds)

    genus = rows[0][2]
    class_counts: dict[str, int] = {}
    total_imgs = 0

    for r in rows:
        cat = r[0] or "unlabeled"
        c = int(r[1])
        class_counts[cat] = c
        total_imgs += c

    counts_list = list(class_counts.values())
    min_c = min(counts_list) if counts_list else 0
    max_c = max(counts_list) if counts_list else 0
    imbalance = round(max_c / max(min_c, 1), 2)

    return DatasetClassDistribution(
        dataset_name=clean_ds,
        genus=genus,
        total_images=total_imgs,
        total_classes=len(class_counts),
        class_counts=class_counts,
        min_class_count=min_c,
        max_class_count=max_c,
        imbalance_ratio=imbalance,
    )


def get_dataset_source_summary(
    db: Session,
    taxon_name: str | None = None,
    dataset_name: str | None = None,
) -> list[SourceSummaryItem]:
    """Returns provenance breakdown of image and record counts grouped by data provider source."""
    try:
        if dataset_name:
            sql = text(
                """
                SELECT sr.Source, COUNT(DISTINCT si.ImageHash) as img_count, COUNT(DISTINCT sr.ShellHash) as shell_count, COUNT(DISTINCT sr.SpeciesHash) as spec_count
                FROM ImageDatasets id
                JOIN ImageTransform it ON it.ID = id.TransformID
                JOIN ShellImages si ON si.ImageHash = it.ImageHash
                JOIN ShellRecord sr ON sr.ShellHash = si.ShellHash
                WHERE id.Dataset = :dataset AND sr.Source IS NOT NULL
                GROUP BY sr.Source
                ORDER BY img_count DESC
                """
            )
            rows = db.execute(sql, {"dataset": dataset_name.strip()}).fetchall()
        elif taxon_name:
            sql = text(
                """
                SELECT sr.Source, COUNT(DISTINCT si.ImageHash) as img_count, COUNT(DISTINCT sr.ShellHash) as shell_count, COUNT(DISTINCT sr.SpeciesHash) as spec_count
                FROM Species s
                JOIN ShellRecord sr ON sr.SpeciesHash = s.SpeciesHash
                JOIN ShellImages si ON si.ShellHash = sr.ShellHash
                WHERE s.SpeciesGenus = :taxon AND sr.Source IS NOT NULL
                GROUP BY sr.Source
                ORDER BY img_count DESC
                """
            )
            rows = db.execute(sql, {"taxon": taxon_name.strip()}).fetchall()
        else:
            sql = text(
                """
                SELECT sr.Source, COUNT(DISTINCT si.ImageHash) as img_count, COUNT(DISTINCT sr.ShellHash) as shell_count, COUNT(DISTINCT sr.SpeciesHash) as spec_count
                FROM ShellRecord sr
                LEFT JOIN ShellImages si ON si.ShellHash = sr.ShellHash
                WHERE sr.Source IS NOT NULL
                GROUP BY sr.Source
                ORDER BY img_count DESC
                LIMIT 50
                """
            )
            rows = db.execute(sql).fetchall()
    except Exception as exc:
        logger.debug("get_dataset_source_summary failed: %s", exc)
        return []

    return [
        SourceSummaryItem(
            source_name=r[0],
            image_count=int(r[1] or 0),
            shell_record_count=int(r[2] or 0),
            species_count=int(r[3] or 0),
        )
        for r in rows
    ]


def get_existing_dataset_versions(
    db: Session,
    taxon_name: str | None = None,
) -> list[DatasetVersionSummary]:
    """Lists registered dataset versions, generator scripts, and transform counts."""
    try:
        if taxon_name:
            sql = text(
                """
                SELECT Dataset, Genus, CreateScript, COUNT(TransformID) as cnt, MIN(CreateDatetime) as created_at, MAX(UpdateDatetime) as updated_at
                FROM ImageDatasets
                WHERE Genus = :taxon OR Dataset LIKE :taxon_like
                GROUP BY Dataset, Genus, CreateScript
                ORDER BY created_at DESC
                """
            )
            rows = db.execute(sql, {"taxon": taxon_name.strip(), "taxon_like": f"%{taxon_name.strip()}%"}).fetchall()
        else:
            sql = text(
                """
                SELECT Dataset, Genus, CreateScript, COUNT(TransformID) as cnt, MIN(CreateDatetime) as created_at, MAX(UpdateDatetime) as updated_at
                FROM ImageDatasets
                GROUP BY Dataset, Genus, CreateScript
                ORDER BY created_at DESC
                LIMIT 100
                """
            )
            rows = db.execute(sql).fetchall()
    except Exception as exc:
        logger.debug("get_existing_dataset_versions failed: %s", exc)
        return []

    return [
        DatasetVersionSummary(
            dataset_name=r[0],
            genus=r[1],
            create_script=r[2],
            total_transforms=int(r[3] or 0),
            created_at=r[4],
            updated_at=r[5],
        )
        for r in rows
    ]


def get_previous_model_summary(
    db: Session,
    taxon_name: str,
) -> list[ModelPerformanceSummary]:
    """Retrieves accuracy, precision, and view types for historical evaluated models for a taxon."""
    clean_taxon = taxon_name.strip()
    try:
        sql = text(
            """
            SELECT Taxon, Model, ViewType, CategoryTaxon, Accuracy, Precision, NumTests, CreateDatetime
            FROM ModelInfo
            WHERE Taxon = :taxon OR Model LIKE :taxon_like
            ORDER BY CreateDatetime DESC
            LIMIT 20
            """
        )
        rows = db.execute(sql, {"taxon": clean_taxon, "taxon_like": f"%{clean_taxon}%"}).fetchall()
    except Exception as exc:
        logger.debug("get_previous_model_summary failed: %s", exc)
        return []

    return [
        ModelPerformanceSummary(
            taxon_name=r[0] or clean_taxon,
            model_name=r[1],
            view_type=r[2],
            category_taxon=r[3],
            accuracy=r[4],
            precision=r[5],
            num_tests=r[6],
            created_at=r[7],
        )
        for r in rows
    ]


def evaluate_classifier_feasibility(
    db: Session,
    request: FeasibilityEvaluationRequest,
) -> FeasibilityEvaluationResponse:
    """Evaluates candidate genera and segregates recommendations into novel candidate targets vs. existing models."""
    genera = get_genus_image_counts(
        db=db,
        family_name=request.family_name,
        order_name=request.order_name,
        class_name=request.class_name,
        min_species=request.min_species,
        min_images_per_species=request.min_images_per_species,
    )

    novel_recommended: list[str] = []
    existing_model_recommended: list[str] = []

    for g in genera:
        is_viable = (
            g.is_feasible_for_classifier
            and g.species_above_threshold >= request.min_species
            and (g.imbalance_ratio <= request.max_imbalance_ratio or g.species_above_threshold >= (request.min_species * 2))
        )
        if is_viable:
            if g.has_existing_model:
                if not request.exclude_existing_models:
                    existing_model_recommended.append(g.genus_name)
            else:
                novel_recommended.append(g.genus_name)

    return FeasibilityEvaluationResponse(
        criteria=request,
        candidate_genera=genera[:35],
        recommended_novel_genera=novel_recommended,
        recommended_existing_model_genera=existing_model_recommended,
        total_genera_evaluated=len(genera),
    )
