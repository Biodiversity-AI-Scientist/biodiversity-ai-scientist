"""
Biodiversity Scientific Semantic Data Type & Domain Catalogue (Phase B01).

Defines:
1. 14 Standardized Biodiversity Research Domains (aligned with EBV dimensions where scientifically applicable).
2. Domain scope decisions:
   - Ecological interaction networks are represented under Community Ecology & Structure.
   - Restoration Ecology is treated as a compositional research programme across populations, communities, ecosystems, and change drivers.
3. Conservation Governance Policy:
   - BAIS computes quantitative inputs (EOO/AOO/trends) and candidate criterion evaluations, but does not represent these as an official IUCN Red List assessment without external human/institutional governance.
4. 4-Tier Capability Scope Governance (generic_core, official_extension, external_tool, identifyshell_specific).
5. 3D Decomposed Maturity & Availability Model:
   - Scope Classification (generic_core, official_extension, external_tool, identifyshell_specific)
   - Availability (installed, not_installed, external)
   - Knowledge Status (known, implemented, validated)
6. Machine-Validatable Semantic Data Type Contracts for biodiversity research inputs/outputs:
   - Additive changes maintain `v1`; breaking structural/semantic changes require `v2`.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class BiodiversityDomain(str, Enum):
    BIODIVERSITY_INFORMATICS = "biodiversity_informatics"
    TAXONOMY_SYSTEMATICS = "taxonomy_systematics"
    SPECIES_POPULATIONS = "species_populations"
    SPECIES_TRAITS = "species_traits"
    GENETIC_COMPOSITION = "genetic_composition"
    COMMUNITY_COMPOSITION = "community_composition"
    EVOLUTION_PHYLOGENETICS = "evolution_phylogenetics"
    ECOSYSTEM_STRUCTURE = "ecosystem_structure"
    ECOSYSTEM_FUNCTION = "ecosystem_function"
    BIOGEOGRAPHY_MACROECOLOGY = "biogeography_macroecology"
    BIODIVERSITY_CHANGE_DRIVERS = "biodiversity_change_drivers"
    CONSERVATION = "conservation"
    INVASION_BIOLOGY = "invasion_biology"
    MOLECULAR_MONITORING_EDNA = "molecular_monitoring_edna"


class EBVDimension(str, Enum):
    GENETIC_COMPOSITION = "genetic_composition"
    SPECIES_POPULATIONS = "species_populations"
    SPECIES_TRAITS = "species_traits"
    COMMUNITY_COMPOSITION = "community_composition"
    ECOSYSTEM_STRUCTURE = "ecosystem_structure"
    ECOSYSTEM_FUNCTION = "ecosystem_function"


class CapabilityScope(str, Enum):
    GENERIC_CORE = "generic_core"
    OFFICIAL_EXTENSION = "official_extension"
    EXTERNAL_TOOL = "external_tool"
    IDENTIFYSHELL_SPECIFIC = "identifyshell_specific"


class KnowledgeStatus(str, Enum):
    KNOWN = "known"
    IMPLEMENTED = "implemented"
    VALIDATED = "validated"


class AvailabilityStatus(str, Enum):
    INSTALLED = "installed"
    NOT_INSTALLED = "not_installed"
    EXTERNAL = "external"


class ScientificMaturity(str, Enum):
    """Legacy single-enum representation maintained for backwards compatibility."""
    KNOWN_METHOD = "known_method"
    INSTALLED = "installed"
    VALIDATED = "validated"
    EXTERNAL_ONLY = "external_only"


@dataclass(frozen=True)
class DomainMetadata:
    domain: BiodiversityDomain
    display_name: str
    description: str
    ebv_dimension: EBVDimension | None
    typical_subdomains: list[str] = field(default_factory=list)


BIODIVERSITY_DOMAINS: dict[str, DomainMetadata] = {
    BiodiversityDomain.BIODIVERSITY_INFORMATICS.value: DomainMetadata(
        domain=BiodiversityDomain.BIODIVERSITY_INFORMATICS,
        display_name="Biodiversity Informatics & Data Quality",
        description="Taxonomic resolution, Darwin Core normalization, data harmonization, coordinate validation, and sampling bias detection.",
        ebv_dimension=None,
        typical_subdomains=["taxonomy_resolution", "data_harmonization", "data_quality", "provenance"],
    ),
    BiodiversityDomain.TAXONOMY_SYSTEMATICS.value: DomainMetadata(
        domain=BiodiversityDomain.TAXONOMY_SYSTEMATICS,
        display_name="Taxonomy & Nomenclature",
        description="Accepted taxonomic identity, synonymy resolution, species delimitation, and multi-evidence taxonomic hypothesis testing.",
        ebv_dimension=EBVDimension.SPECIES_POPULATIONS,
        typical_subdomains=["nomenclature", "synonymy", "species_delimitation", "type_specimens"],
    ),
    BiodiversityDomain.SPECIES_POPULATIONS.value: DomainMetadata(
        domain=BiodiversityDomain.SPECIES_POPULATIONS,
        display_name="Species Populations & Occurrence",
        description="Geographic occurrence records, occupancy mapping, range boundaries, abundance trends, and population monitoring.",
        ebv_dimension=EBVDimension.SPECIES_POPULATIONS,
        typical_subdomains=["occurrence", "distribution", "abundance", "monitoring"],
    ),
    BiodiversityDomain.SPECIES_TRAITS.value: DomainMetadata(
        domain=BiodiversityDomain.SPECIES_TRAITS,
        display_name="Species Traits & Morphology",
        description="Morphometrics, specimen image phenotyping, physiological traits, phenology, and trait covariation.",
        ebv_dimension=EBVDimension.SPECIES_TRAITS,
        typical_subdomains=["morphology", "image_phenomics", "physiology", "phenology", "movement"],
    ),
    BiodiversityDomain.GENETIC_COMPOSITION.value: DomainMetadata(
        domain=BiodiversityDomain.GENETIC_COMPOSITION,
        display_name="Genetic Composition & Diversity",
        description="Allelic diversity, heterozygosity, genetic differentiation (Fst), population structure, and effective population size.",
        ebv_dimension=EBVDimension.GENETIC_COMPOSITION,
        typical_subdomains=["allelic_diversity", "population_structure", "gene_flow", "effective_size"],
    ),
    BiodiversityDomain.COMMUNITY_COMPOSITION.value: DomainMetadata(
        domain=BiodiversityDomain.COMMUNITY_COMPOSITION,
        display_name="Community Ecology & Interaction Networks",
        description="Species richness, Shannon/Simpson diversity indices, community dissimilarity, ecological interaction networks, and turnover.",
        ebv_dimension=EBVDimension.COMMUNITY_COMPOSITION,
        typical_subdomains=["taxonomic_diversity", "functional_diversity", "phylogenetic_diversity", "interaction_networks", "beta_diversity"],
    ),
    BiodiversityDomain.EVOLUTION_PHYLOGENETICS.value: DomainMetadata(
        domain=BiodiversityDomain.EVOLUTION_PHYLOGENETICS,
        display_name="Phylogenetics & Evolutionary Dynamics",
        description="Phylogeny inference, ancestral state reconstruction, phylogenetic independent contrasts, and evolutionary rate estimation.",
        ebv_dimension=EBVDimension.GENETIC_COMPOSITION,
        typical_subdomains=["phylogeny_inference", "trait_evolution", "molecular_dating", "diversification_rates"],
    ),
    BiodiversityDomain.ECOSYSTEM_STRUCTURE.value: DomainMetadata(
        domain=BiodiversityDomain.ECOSYSTEM_STRUCTURE,
        display_name="Ecosystem Structure & Biomes",
        description="Habitat cover, structural complexity, fragmentation indices, and landscape connectivity.",
        ebv_dimension=EBVDimension.ECOSYSTEM_STRUCTURE,
        typical_subdomains=["canopy_structure", "habitat_fragmentation", "connectivity", "land_cover"],
    ),
    BiodiversityDomain.ECOSYSTEM_FUNCTION.value: DomainMetadata(
        domain=BiodiversityDomain.ECOSYSTEM_FUNCTION,
        display_name="Ecosystem Function & Biogeochemistry",
        description="Primary productivity, biomass estimation, phenological cycles, and disturbance dynamics.",
        ebv_dimension=EBVDimension.ECOSYSTEM_FUNCTION,
        typical_subdomains=["primary_productivity", "biomass", "nutrient_cycling", "disturbance"],
    ),
    BiodiversityDomain.BIOGEOGRAPHY_MACROECOLOGY.value: DomainMetadata(
        domain=BiodiversityDomain.BIOGEOGRAPHY_MACROECOLOGY,
        display_name="Biogeography & Macroecology",
        description="Extent of Occurrence (EOO), Area of Occupancy (AOO), latitudinal diversity gradients, range overlap, and bioregionalization.",
        ebv_dimension=EBVDimension.SPECIES_POPULATIONS,
        typical_subdomains=["range_metrics", "bioregions", "species_richness_gradients", "macroecology"],
    ),
    BiodiversityDomain.BIODIVERSITY_CHANGE_DRIVERS.value: DomainMetadata(
        domain=BiodiversityDomain.BIODIVERSITY_CHANGE_DRIVERS,
        display_name="Environmental Drivers & Climate Impacts",
        description="Climate change impact modelling, land-use change attribution, pollution sensitivity, and environmental correlation.",
        ebv_dimension=None,
        typical_subdomains=["climate_change", "habitat_loss", "pollution", "environmental_correlations"],
    ),
    BiodiversityDomain.CONSERVATION.value: DomainMetadata(
        domain=BiodiversityDomain.CONSERVATION,
        display_name="Conservation Status & Red List Governance",
        description="IUCN Red List candidate criteria evaluation, population decline estimation, Key Biodiversity Area identification, and priority setting.",
        ebv_dimension=EBVDimension.SPECIES_POPULATIONS,
        typical_subdomains=["extinction_risk", "iucn_assessment_inputs", "priority_areas", "conservation_planning"],
    ),
    BiodiversityDomain.INVASION_BIOLOGY.value: DomainMetadata(
        domain=BiodiversityDomain.INVASION_BIOLOGY,
        display_name="Invasive Species & Biosecurity",
        description="Alien species range expansion, establishment risk analysis, native species exposure, and invasion velocity.",
        ebv_dimension=EBVDimension.SPECIES_POPULATIONS,
        typical_subdomains=["range_expansion", "exposure_assessment", "impact_evaluation", "biosecurity"],
    ),
    BiodiversityDomain.MOLECULAR_MONITORING_EDNA.value: DomainMetadata(
        domain=BiodiversityDomain.MOLECULAR_MONITORING_EDNA,
        display_name="eDNA & Environmental Genomics",
        description="Environmental DNA detection, metabarcoding amplicon sequencing, OTU/ASV clustering, and molecular taxonomy assignment.",
        ebv_dimension=EBVDimension.COMMUNITY_COMPOSITION,
        typical_subdomains=["metabarcoding", "asv_clustering", "molecular_identification", "edna_monitoring"],
    ),
}


@dataclass(frozen=True)
class SemanticDataType:
    type_key: str
    display_name: str
    category: str
    description: str
    recommended_extension: str | None
    required_fields: list[str] = field(default_factory=list)
    optional_fields: list[str] = field(default_factory=list)
    identifier_semantics: str = ""
    unit_rules: str = ""
    crs: str | None = None
    missingness_policy: str = "Explicit null or omitted for optional fields"
    validation_rules: list[str] = field(default_factory=list)
    sample_structure: dict[str, Any] = field(default_factory=dict)


SEMANTIC_DATA_TYPES: dict[str, SemanticDataType] = {
    "occurrence_dataset_v1": SemanticDataType(
        type_key="occurrence_dataset_v1",
        display_name="Darwin Core Occurrence Table",
        category="geospatial_occurrence",
        description="Tabular biodiversity occurrence observation records aligned with Darwin Core standard. Coordinates can be null in raw ingest datasets.",
        recommended_extension=".csv",
        required_fields=["occurrence_id", "scientific_name"],
        optional_fields=["decimal_latitude", "decimal_longitude", "event_date", "basis_of_record", "coordinate_uncertainty_in_meters", "dataset_id", "elevation_m"],
        identifier_semantics="occurrence_id must be unique across records in the dataset.",
        unit_rules="decimal_latitude and decimal_longitude in decimal degrees. elevation in meters.",
        crs="WGS84 (EPSG:4326) where georeferenced",
        missingness_policy="Coordinates and date may be null in raw datasets; QC validation records coordinate validity status.",
        validation_rules=["Latitude between -90 and 90 when present", "Longitude between -180 and 180 when present", "Date in ISO 8601 format when present"],
        sample_structure={"columns": ["occurrence_id", "scientific_name", "decimal_latitude", "decimal_longitude", "event_date", "basis_of_record"]},
    ),
    "specimen_image_collection_v1": SemanticDataType(
        type_key="specimen_image_collection_v1",
        display_name="Photographic Specimen Collection",
        category="specimen_imaging",
        description="Generic catalog of biological specimen photographs with view metadata, scale information, and taxon concepts.",
        recommended_extension=".json",
        required_fields=["specimen_id", "image_id", "uri"],
        optional_fields=["taxon_id", "view_type", "view_angle", "view_metadata", "scale_information", "capture_metadata"],
        identifier_semantics="image_id is unique; specimen_id identifies physical biological voucher or specimen.",
        unit_rules="scale_information in pixels_per_millimeter where available.",
        crs=None,
        missingness_policy="view_type and view_angle are optional; domain extensions may define specific viewpoints (e.g. apertural, dorsal).",
        validation_rules=["URI must be resolvable or valid relative path", "Image file must exist"],
        sample_structure={"total_images": 500, "manifest": [{"specimen_id": "VOUCH-01", "image_id": "IMG-01", "uri": "specimens/01.jpg", "view_type": "standard"}]},
    ),
    "dense_feature_embedding_v1": SemanticDataType(
        type_key="dense_feature_embedding_v1",
        display_name="Dense Feature Embedding Matrix",
        category="morphological_embeddings",
        description="High-dimensional numerical feature embeddings stored as Parquet/Arrow table with flexible dimensions. Represents intermediate Result/Artifact, not an EvidenceItem.",
        recommended_extension=".parquet",
        required_fields=["entity_id", "vector"],
        optional_fields=["dimension", "model_provenance", "layer_extracted"],
        identifier_semantics="entity_id links embedding back to specimen, occurrence, or sequence.",
        unit_rules="Normalized unit-norm or raw float32 vectors.",
        crs=None,
        missingness_policy="No missing values permitted within embedding vector arrays.",
        validation_rules=["All vectors in a matrix must share identical dimensionality", "Dimension recorded in metadata"],
        sample_structure={"shape": [1000, 384], "embedding_column": "vector", "id_column": "entity_id"},
    ),
    "taxonomic_backbone_v1": SemanticDataType(
        type_key="taxonomic_backbone_v1",
        display_name="Taxonomic Hierarchy & Synonymy Tree",
        category="taxonomy",
        description="Taxonomic tree or concept graph of accepted taxon concepts, basionyms, junior synonyms, and ranks across standard authorities.",
        recommended_extension=".json",
        required_fields=["taxon_id", "canonical_name", "rank", "taxonomic_status"],
        optional_fields=["provider_source", "provider_taxon_id", "parent_taxon_id", "synonyms", "basionym"],
        identifier_semantics="taxon_id is unique within the backbone; provider_taxon_id references authority (WoRMS AphiaID, GBIF ID, NCBI TaxID).",
        unit_rules="Rank follows standardized Linnaean hierarchy.",
        crs=None,
        missingness_policy="parent_taxon_id required except for root kingdoms.",
        validation_rules=["No circular parent-child relationships", "taxonomic_status in ['accepted', 'synonym', 'unresolved']"],
        sample_structure={"taxon_id": 1024, "canonical_name": "Turritella communis", "taxonomic_status": "accepted", "provider_source": "WoRMS", "provider_taxon_id": "141444"},
    ),
    "morphological_trait_table_v1": SemanticDataType(
        type_key="morphological_trait_table_v1",
        display_name="Morphometric & Trait Table",
        category="traits",
        description="Generic continuous and categorical organismal trait and morphometric measurements in long-format.",
        recommended_extension=".parquet",
        required_fields=["trait_observation_id", "entity_id", "trait_id", "value", "unit"],
        optional_fields=["measurement_method", "uncertainty", "sample_size"],
        identifier_semantics="trait_observation_id uniquely identifies the trait measurement; entity_id references specimen, individual organism, or taxon concept.",
        unit_rules="SI units or standardized trait ontology units required.",
        crs=None,
        missingness_policy="Missing trait values represented as NaN/null.",
        validation_rules=["Numeric traits must have valid float values", "Categorical traits match declared ontology terms"],
        sample_structure={"columns": ["trait_observation_id", "entity_id", "trait_id", "value", "unit", "measurement_method"]},
    ),
    "range_polygon_manifest_v1": SemanticDataType(
        type_key="range_polygon_manifest_v1",
        display_name="Species Geographic Range Polygons",
        category="geospatial",
        description="Geospatial polygon representations (Extent of Occurrence alpha hulls, Minimum Convex Polygons, Area of Occupancy grids) in GeoJSON format.",
        recommended_extension=".geojson",
        required_fields=["taxon_id", "geometry"],
        optional_fields=["eoo_km2", "aoo_km2", "method", "convexity_alpha"],
        identifier_semantics="taxon_id links range polygon to taxonomic concept.",
        unit_rules="eoo_km2 and aoo_km2 in square kilometers.",
        crs="WGS84 (EPSG:4326)",
        missingness_policy="Geometry must be valid non-empty Polygon or MultiPolygon.",
        validation_rules=["Geometry must be topologically valid according to OGC simple feature specifications"],
        sample_structure={"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"taxon_id": "T-101", "eoo_km2": 45000}}]},
    ),
    "phylogenetic_tree_v1": SemanticDataType(
        type_key="phylogenetic_tree_v1",
        display_name="Phylogenetic Tree Topology & Branch Lengths",
        category="phylogenetics",
        description="Phylogenetic tree representation with branch lengths, support values, and tip annotations in Newick or Nexus format.",
        recommended_extension=".nwk",
        required_fields=["tree_id", "tree_string", "rooted"],
        optional_fields=["tip_taxon_mapping", "support_type", "model_provenance"],
        identifier_semantics="tree_id identifies dataset object; Tree tips map to taxon_id or specimen_id identifiers.",
        unit_rules="Branch lengths in substitutions per site or time units (Ma).",
        crs=None,
        missingness_policy="All tips must map to valid taxa.",
        validation_rules=["Valid Newick syntax with matching parentheses", "Branch lengths non-negative"],
        sample_structure={"format": "newick", "tree_id": "TREE-01", "tree_string": "((Taxon_A:0.04,Taxon_B:0.05)100:0.08,Taxon_C:0.12);", "rooted": True},
    ),
    "community_abundance_matrix_v1": SemanticDataType(
        type_key="community_abundance_matrix_v1",
        display_name="Site-by-Species Community Matrix",
        category="community_ecology",
        description="Sites (rows) by Species/OTUs (columns) dataset matrix containing counts, biomass, or presence-absence observations.",
        recommended_extension=".csv",
        required_fields=["matrix_id", "site_ids", "species_ids", "abundance_matrix"],
        optional_fields=["metric_type", "sampling_effort", "sampling_protocol"],
        identifier_semantics="matrix_id identifies dataset; site_ids and species_ids identify matrix dimensions.",
        unit_rules="Count, biomass (g/m2), percentage cover, or binary (0/1).",
        crs=None,
        missingness_policy="Unobserved combinations default to zero abundance.",
        validation_rules=["Abundance values non-negative", "Matrix dimensions match len(site_ids) x len(species_ids)"],
        sample_structure={"matrix_id": "COMM-01", "site_ids": ["Site_1", "Site_2"], "species_ids": ["Taxon_A", "Taxon_B"], "abundance_matrix": [[10, 0], [4, 12]]},
    ),
    "genetic_distance_matrix_v1": SemanticDataType(
        type_key="genetic_distance_matrix_v1",
        display_name="Pairwise Genetic Distance Matrix",
        category="population_genetics",
        description="Symmetric matrix dataset of pairwise genetic distances (Fst, Nei's D, or p-distances) between individuals or populations.",
        recommended_extension=".parquet",
        required_fields=["matrix_id", "entity_ids", "distance_metric", "matrix_values"],
        optional_fields=["p_values", "sample_sizes"],
        identifier_semantics="matrix_id identifies distance matrix; entity_ids correspond to population or individual identifiers.",
        unit_rules="Distance metric in declared units (e.g. Fst in [0, 1]).",
        crs=None,
        missingness_policy="Matrix must be complete and symmetric across diagonal.",
        validation_rules=["Diagonal elements equal 0.0", "Matrix must be symmetric (M_ij == M_ji)"],
        sample_structure={"matrix_id": "FST-01", "entity_ids": ["Pop_A", "Pop_B"], "distance_metric": "Fst", "matrix_values": [[0.0, 0.142], [0.142, 0.0]]},
    ),
    "population_time_series_v1": SemanticDataType(
        type_key="population_time_series_v1",
        display_name="Population Abundance Time Series",
        category="species_populations",
        description="Temporal population monitoring observation records for trend, occupancy, and decline estimation.",
        recommended_extension=".csv",
        required_fields=["observation_id", "location_id", "taxon_id", "timestamp", "abundance_or_density"],
        optional_fields=["sampling_effort", "standard_error", "detection_probability"],
        identifier_semantics="observation_id uniquely identifies temporal record; location_id identifies fixed monitoring site; timestamp in ISO 8601.",
        unit_rules="Count, density (individuals/km2), or catch-per-unit-effort (CPUE).",
        crs="WGS84 (EPSG:4326) where spatial coordinates present",
        missingness_policy="Gaps in temporal sampling explicitly recorded with null abundance.",
        validation_rules=["Abundance values non-negative", "Timestamp monotonically increasing per location"],
        sample_structure={"columns": ["observation_id", "location_id", "taxon_id", "timestamp", "abundance_or_density", "sampling_effort"]},
    ),
    "environmental_raster_v1": SemanticDataType(
        type_key="environmental_raster_v1",
        display_name="Environmental & Bioclimatic Raster Covariate",
        category="environmental_covariates",
        description="Spatial raster layers of bioclimatic, topographic, and environmental covariates for species distribution modeling.",
        recommended_extension=".tif",
        required_fields=["raster_layer_id", "variable_name", "spatial_resolution", "bounding_box", "crs", "raster_uri"],
        optional_fields=["nodata_value", "units", "temporal_extent"],
        identifier_semantics="raster_layer_id uniquely identifies raster layer; variable_name references standardized covariate (e.g. bio1_annual_mean_temp).",
        unit_rules="Degrees Celsius, mm precipitation, meters elevation, etc.",
        crs="WGS84 (EPSG:4326) or projected UTM",
        missingness_policy="Nodata pixels must match declared nodata_value.",
        validation_rules=["GeoTIFF file must be readable with valid spatial transform"],
        sample_structure={"raster_layer_id": "BIO-01", "variable_name": "bio1_annual_mean_temp", "spatial_resolution": "30_arcsec", "crs": "EPSG:4326"},
    ),
    "asv_table_v1": SemanticDataType(
        type_key="asv_table_v1",
        display_name="Amplicon Sequence Variant (ASV) Abundance Table",
        category="molecular_monitoring",
        description="Metabarcoding amplicon sequence variant count table with taxonomy assignments and confidence scores.",
        recommended_extension=".parquet",
        required_fields=["sample_id", "asv_id", "read_count", "sequence"],
        optional_fields=["assigned_taxonomy", "confidence_score", "reference_database"],
        identifier_semantics="asv_id identifies unique exact sequence variant (ESV/ASV).",
        unit_rules="Raw read counts or relative abundance fractions.",
        crs=None,
        missingness_policy="Taxonomy assignment can be unclassified at lower ranks if below confidence threshold.",
        validation_rules=["Read counts are positive integers", "Confidence score between 0.0 and 1.0"],
        sample_structure={"columns": ["sample_id", "asv_id", "read_count", "sequence", "assigned_taxonomy"]},
    ),
    "interaction_network_v1": SemanticDataType(
        type_key="interaction_network_v1",
        display_name="Ecological Interaction Network",
        category="community_ecology",
        description="Bipartite or unipartite ecological network representing trophic, mutualistic, or host-parasite interactions.",
        recommended_extension=".json",
        required_fields=["network_id", "source_taxon_id", "target_taxon_id", "interaction_type"],
        optional_fields=["weight", "interaction_strength", "observation_count", "location_id"],
        identifier_semantics="network_id identifies network dataset; source_taxon_id and target_taxon_id map to accepted taxonomic concepts.",
        unit_rules="Weights represent interaction frequency or quantitative biomass flow.",
        crs=None,
        missingness_policy="Unrecorded interactions assume zero or unobserved strength.",
        validation_rules=["interaction_type in ['trophic', 'mutualist', 'host_parasite', 'pollination', 'competition']"],
        sample_structure={"network_id": "NET-01", "nodes": [{"id": "Taxon_1"}], "edges": [{"source": "Taxon_1", "target": "Taxon_2", "type": "trophic", "weight": 4.5}]},
    ),
    "spatial_metric_result_v1": SemanticDataType(
        type_key="spatial_metric_result_v1",
        display_name="Spatial Metric & Conservation Indices",
        category="conservation_biogeography",
        description="Structured numeric results for spatial conservation assessments (e.g. EOO, AOO, fragmentation metrics).",
        recommended_extension=".json",
        required_fields=["metric_id", "taxon_id", "eoo_km2", "aoo_km2", "criterion_b_candidate"],
        optional_fields=["subpopulation_count", "severely_fragmented", "continuing_decline_evidence"],
        identifier_semantics="metric_id identifies result record; taxon_id links result to assessed biological taxon.",
        unit_rules="Square kilometers for spatial areas.",
        crs="WGS84 (EPSG:4326)",
        missingness_policy="Evaluations indicate 'data_deficient' if occurrences are insufficient for calculation.",
        validation_rules=["Area metrics must be non-negative numbers"],
        sample_structure={"metric_id": "METRIC-01", "taxon_id": "T-101", "eoo_km2": 18200.5, "aoo_km2": 48.0, "criterion_b_candidate": "Vulnerable"},
    ),
}
