"""
Biodiversity Capability Registry Seed Service (Phase B01).

Populates the ScientificApplication and ScientificCapability tables with:
1. Two-tier architecture: ScientificCapability (generic method) with CapabilityImplementation binding.
2. 14 Standardized Biodiversity Research Domains.
3. 4-Tier Scope Governance (generic_core, official_extension, external_tool, identifyshell_specific).
4. Decomposed 3D Maturity (knowledge_status, availability, scope).
5. Comprehensive contracts (preconditions, scientific assumptions, constraints, semantic I/O, evidence types).
"""
from typing import Any
from sqlalchemy.orm import Session

from src.core.contracts.semantic_types import (
    AvailabilityStatus,
    BiodiversityDomain,
    CapabilityScope,
    EBVDimension,
    KnowledgeStatus,
    ScientificMaturity,
)
from src.models import ScientificApplication, ScientificCapability


SEED_APPLICATIONS: list[dict[str, Any]] = [
    {
        "name": "bais_core_platform",
        "display_name": "BAIS Generic Core Platform",
        "category": "core_platform",
        "description": "Standard built-in biodiversity informatics, statistical, and ecological computing routines.",
        "host_environment": "bais_worker",
        "invocation_type": "in_process",
        "is_gpu_required": False,
        "is_enabled": True,
    },
    {
        "name": "identifyshell_suite",
        "display_name": "IdentifyShell Research Suite",
        "category": "identifyshell_integration",
        "description": "IdentifyShell deep learning pipelines, GPU workers, and specimen vision models.",
        "host_environment": "gpu_cluster_worker",
        "invocation_type": "gpu_dispatch",
        "is_gpu_required": True,
        "is_enabled": True,
    },
    {
        "name": "bais_biodiversity_extensions",
        "display_name": "Official Biodiversity Extension Pack",
        "category": "official_extension",
        "description": "Specialist macroecology, phylogenetics, population genetics, and SDM extension modules.",
        "host_environment": "extension_container",
        "invocation_type": "container_job",
        "is_gpu_required": False,
        "is_enabled": True,
    },
    {
        "name": "external_specialist_tools",
        "display_name": "External Scientific Applications",
        "category": "external_tool",
        "description": "Contracts for standalone phylogenetic, genomic, and remote sensing software.",
        "host_environment": "external_binary",
        "invocation_type": "cli_script",
        "is_gpu_required": False,
        "is_enabled": True,
    },
]

SEED_CAPABILITIES: list[dict[str, Any]] = [
    # ----------------------------------------------------
    # 1. BIODIVERSITY INFORMATICS & DATA QUALITY
    # ----------------------------------------------------
    {
        "app_name": "bais_core_platform",
        "capability_key": "validate_occurrences",
        "display_name": "Occurrence Data Quality & Coordinate Validation",
        "scientific_purpose": "Validates Darwin Core records for valid decimal coordinates, non-zero values, plausible dates, and country-boundary concordance.",
        "domain": BiodiversityDomain.BIODIVERSITY_INFORMATICS.value,
        "subdomain": "data_quality",
        "ebv_dimension": None,
        "capability_scope": CapabilityScope.GENERIC_CORE.value,
        "is_generic": True,
        "scientific_maturity": ScientificMaturity.INSTALLED.value,
        "knowledge_status": KnowledgeStatus.VALIDATED.value,
        "availability": AvailabilityStatus.INSTALLED.value,
        "input_types": [{"type": "occurrence_dataset_v1"}],
        "output_types": [{"type": "occurrence_dataset_v1"}],
        "expected_evidence_types": ["data_quality_audit", "spatial_concordance_metric"],
        "preconditions": ["Input is tabular occurrence dataset", "Columns latitude and longitude exist"],
        "scientific_assumptions": ["WGS84 coordinate reference system", "ISO 8601 timestamps"],
        "scientific_constraints": ["Memory scales with record count"],
        "default_parameters": {"check_zero_coordinates": True, "check_inverted_coords": True},
        "implementations": [
            {
                "implementation_key": "bais_dwc_validator_v1",
                "display_name": "BAIS Builtin Darwin Core Validator",
                "provider": "bais_core",
                "adapter_module": "src.adapters.dwc_validator",
                "backend_environment": "local_worker",
                "runtime_version": "1.2.0",
                "availability": AvailabilityStatus.INSTALLED.value,
                "validation_status": KnowledgeStatus.VALIDATED.value,
                "is_default": True,
            }
        ],
    },
    {
        "app_name": "bais_core_platform",
        "capability_key": "resolve_taxonomic_names_worms",
        "display_name": "WoRMS / Marine Taxonomy Resolution",
        "scientific_purpose": "Resolves scientific names against World Register of Marine Species to retrieve accepted AphiaIDs, valid names, and higher classification.",
        "domain": BiodiversityDomain.BIODIVERSITY_INFORMATICS.value,
        "subdomain": "taxonomy_resolution",
        "ebv_dimension": None,
        "capability_scope": CapabilityScope.GENERIC_CORE.value,
        "is_generic": True,
        "scientific_maturity": ScientificMaturity.INSTALLED.value,
        "knowledge_status": KnowledgeStatus.VALIDATED.value,
        "availability": AvailabilityStatus.INSTALLED.value,
        "input_types": [{"type": "taxonomic_name_list_v1"}],
        "output_types": [{"type": "taxonomic_backbone_v1"}],
        "expected_evidence_types": ["taxonomic_resolution_summary"],
        "preconditions": ["Names formatted as UTF-8 binomial strings"],
        "scientific_assumptions": ["WoRMS backbone represents accepted marine taxonomic authority"],
        "default_parameters": {"fuzzy_matching": True, "marine_only": False},
        "implementations": [
            {
                "implementation_key": "worms_rest_resolver_v1",
                "display_name": "WoRMS REST API Resolver",
                "provider": "vliz_worms",
                "adapter_module": "src.adapters.worms_client",
                "backend_environment": "external_api",
                "runtime_version": "rest_v1",
                "availability": AvailabilityStatus.INSTALLED.value,
                "validation_status": KnowledgeStatus.VALIDATED.value,
                "is_default": True,
            }
        ],
    },
    {
        "app_name": "bais_core_platform",
        "capability_key": "assess_sampling_bias",
        "display_name": "Spatial & Temporal Sampling Bias Assessment",
        "scientific_purpose": "Computes spatial nearest-neighbor distance distributions and temporal collection effort curves to detect geographic clustering and collector bias.",
        "domain": BiodiversityDomain.BIODIVERSITY_INFORMATICS.value,
        "subdomain": "data_quality",
        "ebv_dimension": None,
        "capability_scope": CapabilityScope.GENERIC_CORE.value,
        "is_generic": True,
        "scientific_maturity": ScientificMaturity.INSTALLED.value,
        "knowledge_status": KnowledgeStatus.IMPLEMENTED.value,
        "availability": AvailabilityStatus.INSTALLED.value,
        "input_types": [{"type": "occurrence_dataset_v1"}],
        "output_types": [{"type": "bias_metric_report_v1"}],
        "expected_evidence_types": ["sampling_bias_index", "clumping_statistic"],
        "preconditions": ["Minimum 10 distinct occurrence points"],
        "scientific_assumptions": ["Target taxon distribution sampled non-uniformly"],
        "default_parameters": {"grid_cell_size_deg": 0.5, "temporal_bin": "decade"},
        "implementations": [
            {
                "implementation_key": "spatial_bias_estimator_v1",
                "display_name": "Spatial Nearest-Neighbor Bias Estimator",
                "provider": "bais_stats",
                "adapter_module": "src.adapters.bias_estimator",
                "backend_environment": "local_worker",
                "runtime_version": "0.9.1",
                "availability": AvailabilityStatus.INSTALLED.value,
                "validation_status": KnowledgeStatus.IMPLEMENTED.value,
                "is_default": True,
            }
        ],
    },

    # ----------------------------------------------------
    # 2. TAXONOMY & NOMENCLATURE
    # ----------------------------------------------------
    {
        "app_name": "bais_core_platform",
        "capability_key": "evaluate_species_delimitation",
        "display_name": "Multi-Evidence Species Delimitation",
        "scientific_purpose": "Integrates morphological divergence, genetic distance, and geographic sympatry to test unified species hypothesis boundaries.",
        "domain": BiodiversityDomain.TAXONOMY_SYSTEMATICS.value,
        "subdomain": "species_delimitation",
        "ebv_dimension": EBVDimension.SPECIES_POPULATIONS.value,
        "capability_scope": CapabilityScope.GENERIC_CORE.value,
        "is_generic": True,
        "scientific_maturity": ScientificMaturity.KNOWN_METHOD.value,
        "knowledge_status": KnowledgeStatus.KNOWN.value,
        "availability": AvailabilityStatus.NOT_INSTALLED.value,
        "input_types": [{"type": "morphological_trait_table_v1"}, {"type": "genetic_distance_matrix_v1"}],
        "output_types": [{"type": "species_boundary_report_v1"}],
        "expected_evidence_types": ["delimitation_support_score", "concordance_statistic"],
        "preconditions": ["Matched specimen identifiers across morphology and genetics"],
        "scientific_assumptions": ["Coalescent lineage independence"],
        "default_parameters": {"confidence_threshold": 0.95},
        "implementations": [],
    },

    # ----------------------------------------------------
    # 3. SPECIES POPULATIONS & OCCURRENCE
    # ----------------------------------------------------
    {
        "app_name": "bais_core_platform",
        "capability_key": "calculate_species_richness",
        "display_name": "Species Richness & Abundance Aggregation",
        "scientific_purpose": "Aggregates occurrence records across spatial grid cells to calculate observed taxonomic richness, unique counts, and sampling density.",
        "domain": BiodiversityDomain.SPECIES_POPULATIONS.value,
        "subdomain": "distribution",
        "ebv_dimension": EBVDimension.SPECIES_POPULATIONS.value,
        "capability_scope": CapabilityScope.GENERIC_CORE.value,
        "is_generic": True,
        "scientific_maturity": ScientificMaturity.INSTALLED.value,
        "knowledge_status": KnowledgeStatus.VALIDATED.value,
        "availability": AvailabilityStatus.INSTALLED.value,
        "input_types": [{"type": "occurrence_dataset_v1"}],
        "output_types": [{"type": "richness_grid_v1"}],
        "expected_evidence_types": ["species_richness_count", "grid_cell_abundance_table"],
        "preconditions": ["Georeferenced occurrence dataset"],
        "scientific_assumptions": ["Spatial aggregation reflects ecological presence"],
        "default_parameters": {"grid_size_km": 50, "min_occurrences_per_cell": 1},
        "implementations": [
            {
                "implementation_key": "richness_gridding_v1",
                "display_name": "Spatial Grid Richness Calculator",
                "provider": "bais_geo",
                "adapter_module": "src.adapters.richness_gridding",
                "backend_environment": "local_worker",
                "runtime_version": "1.0.0",
                "availability": AvailabilityStatus.INSTALLED.value,
                "validation_status": KnowledgeStatus.VALIDATED.value,
                "is_default": True,
            }
        ],
    },
    {
        "app_name": "bais_core_platform",
        "capability_key": "estimate_population_trends",
        "display_name": "Population Time-Series Trend & Decline Estimation",
        "scientific_purpose": "Fits generalized linear and GAM models to temporal monitoring data to calculate annual percentage rates of population change.",
        "domain": BiodiversityDomain.SPECIES_POPULATIONS.value,
        "subdomain": "monitoring",
        "ebv_dimension": EBVDimension.SPECIES_POPULATIONS.value,
        "capability_scope": CapabilityScope.GENERIC_CORE.value,
        "is_generic": True,
        "scientific_maturity": ScientificMaturity.INSTALLED.value,
        "knowledge_status": KnowledgeStatus.IMPLEMENTED.value,
        "availability": AvailabilityStatus.INSTALLED.value,
        "input_types": [{"type": "population_time_series_v1"}],
        "output_types": [{"type": "trend_model_summary_v1"}],
        "expected_evidence_types": ["annual_rate_of_change", "decline_percentage_3_gen"],
        "preconditions": ["Minimum 3 temporal timepoints per population unit"],
        "scientific_assumptions": ["Consistent sampling methodology across survey intervals"],
        "default_parameters": {"model_family": "poisson", "smooth_terms": True},
        "implementations": [
            {
                "implementation_key": "gam_population_trend_v1",
                "display_name": "GAM Temporal Population Trend Estimator",
                "provider": "bais_stats",
                "adapter_module": "src.adapters.population_trend",
                "backend_environment": "local_worker",
                "runtime_version": "1.1.0",
                "availability": AvailabilityStatus.INSTALLED.value,
                "validation_status": KnowledgeStatus.IMPLEMENTED.value,
                "is_default": True,
            }
        ],
    },

    # ----------------------------------------------------
    # 4. SPECIES TRAITS & MORPHOLOGY
    # ----------------------------------------------------
    {
        "app_name": "identifyshell_suite",
        "capability_key": "extract_image_embeddings",
        "display_name": "Organismal Specimen Vision Feature Extraction",
        "scientific_purpose": "Generic method to extract dense high-dimensional semantic feature representations from organism specimen images using visual foundation models. Intermediate Result/Artifact for subsequent phenomic ordination.",
        "domain": BiodiversityDomain.SPECIES_TRAITS.value,
        "subdomain": "image_phenomics",
        "ebv_dimension": EBVDimension.SPECIES_TRAITS.value,
        "capability_scope": CapabilityScope.GENERIC_CORE.value,
        "is_generic": True,
        "scientific_maturity": ScientificMaturity.INSTALLED.value,
        "knowledge_status": KnowledgeStatus.VALIDATED.value,
        "availability": AvailabilityStatus.INSTALLED.value,
        "input_types": [{"type": "specimen_image_collection_v1"}],
        "output_types": [{"type": "dense_feature_embedding_v1"}],
        "expected_evidence_types": [],
        "preconditions": ["Specimen images readable (JPG/PNG)", "Batch size fits available RAM/VRAM"],
        "scientific_assumptions": ["Visual representations correlate with phenotypic traits"],
        "scientific_constraints": ["Memory limits batch size"],
        "default_parameters": {"model_checkpoint": "dinov3_vitb14", "batch_size": 32},
        "implementations": [
            {
                "implementation_key": "identifyshell_dinov3_v1",
                "display_name": "IdentifyShell DINOv3 Specimen Embedding Runner",
                "provider": "identifyshell_gpu",
                "adapter_module": "src.adapters.identifyshell_dinov3",
                "backend_environment": "gpu_cluster",
                "runtime_version": "3.2.0",
                "implementation_scope": CapabilityScope.IDENTIFYSHELL_SPECIFIC.value,
                "availability": AvailabilityStatus.INSTALLED.value,
                "validation_status": KnowledgeStatus.VALIDATED.value,
                "is_default": True,
            },
            {
                "implementation_key": "bioclip_adapter_v1",
                "display_name": "BioCLIP Standard Taxonomic Vision Adapter",
                "provider": "open_bioclip",
                "adapter_module": "src.adapters.bioclip",
                "backend_environment": "local_host",
                "runtime_version": "1.0.0",
                "implementation_scope": CapabilityScope.OFFICIAL_EXTENSION.value,
                "availability": AvailabilityStatus.INSTALLED.value,
                "validation_status": KnowledgeStatus.IMPLEMENTED.value,
                "is_default": False,
            },
        ],
    },
    {
        "app_name": "bais_core_platform",
        "capability_key": "analyze_morphometrics",
        "display_name": "Multivariate Morphological Trait Analysis",
        "scientific_purpose": "Computes Principal Component Analysis (PCA) and morphological disparity metrics on continuous trait tables.",
        "domain": BiodiversityDomain.SPECIES_TRAITS.value,
        "subdomain": "morphology",
        "ebv_dimension": EBVDimension.SPECIES_TRAITS.value,
        "capability_scope": CapabilityScope.GENERIC_CORE.value,
        "is_generic": True,
        "scientific_maturity": ScientificMaturity.INSTALLED.value,
        "knowledge_status": KnowledgeStatus.VALIDATED.value,
        "availability": AvailabilityStatus.INSTALLED.value,
        "input_types": [{"type": "morphological_trait_table_v1"}],
        "output_types": [{"type": "morphospace_ordination_v1"}],
        "expected_evidence_types": ["pca_variance_explained", "morphological_disparity_index"],
        "preconditions": ["Numeric trait columns without complete null vectors"],
        "scientific_assumptions": ["Morphological variance reflects phenotypic divergence"],
        "default_parameters": {"scale_features": True, "num_components": 5},
        "implementations": [
            {
                "implementation_key": "sklearn_morphometrics_pca_v1",
                "display_name": "Scikit-Learn Trait PCA & Disparity Engine",
                "provider": "bais_stats",
                "adapter_module": "src.adapters.trait_pca",
                "backend_environment": "local_worker",
                "runtime_version": "1.4.2",
                "availability": AvailabilityStatus.INSTALLED.value,
                "validation_status": KnowledgeStatus.VALIDATED.value,
                "is_default": True,
            }
        ],
    },

    # ----------------------------------------------------
    # 5. GENETIC COMPOSITION & DIVERSITY
    # ----------------------------------------------------
    {
        "app_name": "bais_biodiversity_extensions",
        "capability_key": "calculate_genetic_differentiation",
        "display_name": "Pairwise Population Genetic Differentiation (Fst)",
        "scientific_purpose": "Calculates Weir and Cockerham pairwise Fst and Nei's genetic distance matrix across spatial subpopulations.",
        "domain": BiodiversityDomain.GENETIC_COMPOSITION.value,
        "subdomain": "population_structure",
        "ebv_dimension": EBVDimension.GENETIC_COMPOSITION.value,
        "capability_scope": CapabilityScope.OFFICIAL_EXTENSION.value,
        "is_generic": True,
        "scientific_maturity": ScientificMaturity.INSTALLED.value,
        "knowledge_status": KnowledgeStatus.IMPLEMENTED.value,
        "availability": AvailabilityStatus.INSTALLED.value,
        "input_types": [{"type": "vcf_genotype_matrix_v1"}],
        "output_types": [{"type": "genetic_distance_matrix_v1"}],
        "expected_evidence_types": ["pairwise_fst_matrix", "heterozygosity_summary"],
        "preconditions": ["Biallelic SNP genotype matrix with population identifiers"],
        "scientific_assumptions": ["Hardy-Weinberg equilibrium in reference demes"],
        "default_parameters": {"min_maf": 0.05, "missing_genotype_threshold": 0.2},
        "implementations": [
            {
                "implementation_key": "scikit_allel_fst_v1",
                "display_name": "Scikit-Allel Population Differentiation Engine",
                "provider": "bais_genomics",
                "adapter_module": "src.adapters.popgen_allel",
                "backend_environment": "local_worker",
                "runtime_version": "1.3.7",
                "availability": AvailabilityStatus.INSTALLED.value,
                "validation_status": KnowledgeStatus.IMPLEMENTED.value,
                "is_default": True,
            }
        ],
    },

    # ----------------------------------------------------
    # 6. COMMUNITY ECOLOGY & INTERACTION NETWORKS
    # ----------------------------------------------------
    {
        "app_name": "bais_core_platform",
        "capability_key": "calculate_alpha_beta_diversity",
        "display_name": "Alpha & Beta Diversity Partitioning",
        "scientific_purpose": "Calculates Shannon diversity, Simpson index, Pielou evenness, and Bray-Curtis dissimilarity ordination across ecological sites.",
        "domain": BiodiversityDomain.COMMUNITY_COMPOSITION.value,
        "subdomain": "beta_diversity",
        "ebv_dimension": EBVDimension.COMMUNITY_COMPOSITION.value,
        "capability_scope": CapabilityScope.GENERIC_CORE.value,
        "is_generic": True,
        "scientific_maturity": ScientificMaturity.INSTALLED.value,
        "knowledge_status": KnowledgeStatus.VALIDATED.value,
        "availability": AvailabilityStatus.INSTALLED.value,
        "input_types": [{"type": "community_abundance_matrix_v1"}],
        "output_types": [{"type": "diversity_indices_table_v1"}],
        "expected_evidence_types": ["shannon_diversity_h", "bray_curtis_dissimilarity"],
        "preconditions": ["Sites-by-species matrix with non-negative counts"],
        "scientific_assumptions": ["Equal sampling effort across analyzed sites"],
        "default_parameters": {"metrics": ["shannon", "simpson", "bray_curtis"]},
        "implementations": [
            {
                "implementation_key": "scipy_community_diversity_v1",
                "display_name": "SciPy/Scikit-Bio Community Diversity Package",
                "provider": "bais_stats",
                "adapter_module": "src.adapters.community_diversity",
                "backend_environment": "local_worker",
                "runtime_version": "1.12.0",
                "availability": AvailabilityStatus.INSTALLED.value,
                "validation_status": KnowledgeStatus.VALIDATED.value,
                "is_default": True,
            }
        ],
    },
    {
        "app_name": "bais_biodiversity_extensions",
        "capability_key": "analyze_interaction_networks",
        "display_name": "Ecological Interaction Network Modularity & Connectance",
        "scientific_purpose": "Calculates network connectance, nestedness (NODF), modularity (Q), and species centrality on bipartite/unipartite ecological interaction graphs.",
        "domain": BiodiversityDomain.COMMUNITY_COMPOSITION.value,
        "subdomain": "interaction_networks",
        "ebv_dimension": EBVDimension.COMMUNITY_COMPOSITION.value,
        "capability_scope": CapabilityScope.OFFICIAL_EXTENSION.value,
        "is_generic": True,
        "scientific_maturity": ScientificMaturity.INSTALLED.value,
        "knowledge_status": KnowledgeStatus.IMPLEMENTED.value,
        "availability": AvailabilityStatus.INSTALLED.value,
        "input_types": [{"type": "interaction_network_v1"}],
        "output_types": [{"type": "network_topology_summary_v1"}],
        "expected_evidence_types": ["connectance_metric", "nestedness_nodf", "modularity_q"],
        "preconditions": ["Valid interaction edge list"],
        "scientific_assumptions": ["Observed links represent persistent ecological interactions"],
        "default_parameters": {"null_model": "vazquez", "permutations": 1000},
        "implementations": [
            {
                "implementation_key": "networkx_ecological_networks_v1",
                "display_name": "NetworkX Ecological Network Topology Analyzer",
                "provider": "bais_networks",
                "adapter_module": "src.adapters.network_analyzer",
                "backend_environment": "local_worker",
                "runtime_version": "3.2.1",
                "availability": AvailabilityStatus.INSTALLED.value,
                "validation_status": KnowledgeStatus.IMPLEMENTED.value,
                "is_default": True,
            }
        ],
    },

    # ----------------------------------------------------
    # 7. PHYLOGENETICS & EVOLUTIONARY DYNAMICS
    # ----------------------------------------------------
    {
        "app_name": "external_specialist_tools",
        "capability_key": "infer_phylogeny",
        "display_name": "Maximum Likelihood Phylogeny Inference",
        "scientific_purpose": "Generic method to construct phylogenetic trees from aligned multi-locus nucleotide or amino acid sequences using maximum likelihood or Bayesian methods.",
        "domain": BiodiversityDomain.EVOLUTION_PHYLOGENETICS.value,
        "subdomain": "phylogeny_inference",
        "ebv_dimension": EBVDimension.GENETIC_COMPOSITION.value,
        "capability_scope": CapabilityScope.EXTERNAL_TOOL.value,
        "is_generic": True,
        "scientific_maturity": ScientificMaturity.INSTALLED.value,
        "knowledge_status": KnowledgeStatus.VALIDATED.value,
        "availability": AvailabilityStatus.EXTERNAL.value,
        "input_types": [{"type": "multiple_sequence_alignment_v1"}],
        "output_types": [{"type": "phylogenetic_tree_v1"}],
        "expected_evidence_types": ["newick_tree_string", "ultrafast_bootstrap_supports"],
        "preconditions": ["FASTA/Phylip formatted alignment", "Valid substitution model declaration"],
        "scientific_assumptions": ["Sites evolve independently under chosen model"],
        "default_parameters": {"model": "MFP", "bootstrap_replicates": 1000},
        "implementations": [
            {
                "implementation_key": "iqtree_v2",
                "display_name": "IQ-TREE 2 Multithreaded Phylogeny Suite",
                "provider": "iqtree_org",
                "adapter_module": "src.adapters.iqtree_runner",
                "backend_environment": "external_binary",
                "runtime_version": "2.2.6",
                "availability": AvailabilityStatus.EXTERNAL.value,
                "validation_status": KnowledgeStatus.VALIDATED.value,
                "is_default": True,
            }
        ],
    },

    # ----------------------------------------------------
    # 8. BIOGEOGRAPHY & MACROECOLOGY
    # ----------------------------------------------------
    {
        "app_name": "bais_core_platform",
        "capability_key": "calculate_extent_of_occurrence",
        "display_name": "Geospatial Extent of Occurrence (EOO) & Area of Occupancy (AOO)",
        "scientific_purpose": "Constructs minimum convex polygons (MCP) and alpha-hulls around verified occurrence records to compute geographic EOO and 2x2km grid AOO.",
        "domain": BiodiversityDomain.BIOGEOGRAPHY_MACROECOLOGY.value,
        "subdomain": "range_metrics",
        "ebv_dimension": EBVDimension.SPECIES_POPULATIONS.value,
        "capability_scope": CapabilityScope.GENERIC_CORE.value,
        "is_generic": True,
        "scientific_maturity": ScientificMaturity.INSTALLED.value,
        "knowledge_status": KnowledgeStatus.VALIDATED.value,
        "availability": AvailabilityStatus.INSTALLED.value,
        "input_types": [{"type": "occurrence_dataset_v1"}],
        "output_types": [{"type": "spatial_metric_result_v1"}, {"type": "range_polygon_manifest_v1"}],
        "expected_evidence_types": ["eoo_km2_value", "aoo_2x2km_value", "range_polygon_geojson"],
        "preconditions": ["Minimum 3 non-collinear spatial occurrence records"],
        "scientific_assumptions": ["WGS84 ellipsoidal area geodesic projection"],
        "default_parameters": {"aoo_cell_width_km": 2.0, "exclude_marine_for_terrestrial": True},
        "implementations": [
            {
                "implementation_key": "geospatial_shapely_eoo_v1",
                "display_name": "Shapely / GeoPandas EOO/AOO Calculation Engine",
                "provider": "bais_geospatial",
                "adapter_module": "src.adapters.shapely_eoo",
                "backend_environment": "local_worker",
                "runtime_version": "2.0.4",
                "availability": AvailabilityStatus.INSTALLED.value,
                "validation_status": KnowledgeStatus.VALIDATED.value,
                "is_default": True,
            }
        ],
    },
    {
        "app_name": "bais_biodiversity_extensions",
        "capability_key": "fit_species_distribution_model",
        "display_name": "Species Distribution Modelling (SDM / MaxEnt)",
        "scientific_purpose": "Generic method to fit ecological niche models linking presence-background occurrences with environmental and bioclimatic raster grids.",
        "domain": BiodiversityDomain.BIOGEOGRAPHY_MACROECOLOGY.value,
        "subdomain": "macroecology",
        "ebv_dimension": EBVDimension.SPECIES_POPULATIONS.value,
        "capability_scope": CapabilityScope.OFFICIAL_EXTENSION.value,
        "is_generic": True,
        "scientific_maturity": ScientificMaturity.INSTALLED.value,
        "knowledge_status": KnowledgeStatus.IMPLEMENTED.value,
        "availability": AvailabilityStatus.INSTALLED.value,
        "input_types": [{"type": "occurrence_dataset_v1"}, {"type": "environmental_raster_v1"}],
        "output_types": [{"type": "habitat_suitability_raster_v1"}],
        "expected_evidence_types": ["auc_roc_statistic", "variable_importance_table"],
        "preconditions": ["Georeferenced occurrence points", "Aligned environmental raster stack"],
        "scientific_assumptions": ["Species is in equilibrium with its bioclimatic niche"],
        "default_parameters": {"algorithm": "maxent", "background_points": 10000},
        "implementations": [
            {
                "implementation_key": "maxent_cloglog_v3",
                "display_name": "MaxEnt ClogLog Ecological Niche Model",
                "provider": "bais_sdm",
                "adapter_module": "src.adapters.maxent_sdm",
                "backend_environment": "local_worker",
                "runtime_version": "3.4.4",
                "availability": AvailabilityStatus.INSTALLED.value,
                "validation_status": KnowledgeStatus.IMPLEMENTED.value,
                "is_default": True,
            }
        ],
    },

    # ----------------------------------------------------
    # 9. CONSERVATION STATUS & RED LIST GOVERNANCE
    # ----------------------------------------------------
    {
        "app_name": "bais_core_platform",
        "capability_key": "evaluate_iucn_criterion_b",
        "display_name": "IUCN Red List Criterion B Candidate Assessment",
        "scientific_purpose": "Evaluates geographic range metrics against quantitative IUCN Criterion B thresholds (B1 EOO < 20,000 km2, B2 AOO < 2,000 km2) and subcriterion prerequisites.",
        "domain": BiodiversityDomain.CONSERVATION.value,
        "subdomain": "iucn_assessment_inputs",
        "ebv_dimension": EBVDimension.SPECIES_POPULATIONS.value,
        "capability_scope": CapabilityScope.GENERIC_CORE.value,
        "is_generic": True,
        "scientific_maturity": ScientificMaturity.INSTALLED.value,
        "knowledge_status": KnowledgeStatus.VALIDATED.value,
        "availability": AvailabilityStatus.INSTALLED.value,
        "input_types": [{"type": "spatial_metric_result_v1"}],
        "output_types": [{"type": "iucn_candidate_evaluation_v1"}],
        "expected_evidence_types": ["candidate_threat_category", "criterion_b_diagnostic_summary"],
        "preconditions": ["Computed EOO or AOO metric available"],
        "scientific_assumptions": ["Evaluation provides candidate criteria inputs; official status requires institutional governance"],
        "default_parameters": {"evaluate_subcriteria": True},
        "implementations": [
            {
                "implementation_key": "bais_iucn_evaluator_v1",
                "display_name": "BAIS IUCN Criterion B Quantitative Evaluator",
                "provider": "bais_conservation",
                "adapter_module": "src.adapters.iucn_evaluator",
                "backend_environment": "local_worker",
                "runtime_version": "1.0.0",
                "availability": AvailabilityStatus.INSTALLED.value,
                "validation_status": KnowledgeStatus.VALIDATED.value,
                "is_default": True,
            }
        ],
    },

    # ----------------------------------------------------
    # 10. EDNA & ENVIRONMENTAL GENOMICS
    # ----------------------------------------------------
    {
        "app_name": "bais_biodiversity_extensions",
        "capability_key": "cluster_metabarcode_asvs",
        "display_name": "eDNA Amplicon Sequence Variant (ASV) Denoising & Clustering",
        "scientific_purpose": "Denoises raw metabarcoding reads into exact sequence variants (ASVs) and assigns taxonomic identities against reference barcode backbones.",
        "domain": BiodiversityDomain.MOLECULAR_MONITORING_EDNA.value,
        "subdomain": "metabarcoding",
        "ebv_dimension": EBVDimension.COMMUNITY_COMPOSITION.value,
        "capability_scope": CapabilityScope.OFFICIAL_EXTENSION.value,
        "is_generic": True,
        "scientific_maturity": ScientificMaturity.INSTALLED.value,
        "knowledge_status": KnowledgeStatus.IMPLEMENTED.value,
        "availability": AvailabilityStatus.INSTALLED.value,
        "input_types": [{"type": "demultiplexed_fastq_v1"}],
        "output_types": [{"type": "asv_table_v1"}],
        "expected_evidence_types": ["asv_read_count_table", "taxonomic_confidence_scores"],
        "preconditions": ["Demultiplexed paired-end FASTQ files with primers removed"],
        "scientific_assumptions": ["DADA2 error model distinguishes biological variants from sequencing noise"],
        "default_parameters": {"trim_length": 240, "max_ee": 2},
        "implementations": [
            {
                "implementation_key": "dada2_asv_pipeline_v1",
                "display_name": "DADA2 / VSEARCH eDNA Amplicon Denoising Pipeline",
                "provider": "bais_edna",
                "adapter_module": "src.adapters.dada2_pipeline",
                "backend_environment": "local_worker",
                "runtime_version": "1.28.0",
                "availability": AvailabilityStatus.INSTALLED.value,
                "validation_status": KnowledgeStatus.IMPLEMENTED.value,
                "is_default": True,
            }
        ],
    },

    # ----------------------------------------------------
    # 11. ECOSYSTEM STRUCTURE & BIOMES
    # ----------------------------------------------------
    {
        "app_name": "bais_biodiversity_extensions",
        "capability_key": "calculate_canopy_and_habitat_metrics",
        "display_name": "Canopy Height & Habitat Fragmentation Analysis",
        "scientific_purpose": "Derives structural habitat complexity, edge-to-interior ratios, and canopy height metrics from satellite or LiDAR rasters.",
        "domain": BiodiversityDomain.ECOSYSTEM_STRUCTURE.value,
        "subdomain": "habitat_fragmentation",
        "ebv_dimension": EBVDimension.ECOSYSTEM_STRUCTURE.value,
        "capability_scope": CapabilityScope.OFFICIAL_EXTENSION.value,
        "is_generic": True,
        "scientific_maturity": ScientificMaturity.INSTALLED.value,
        "knowledge_status": KnowledgeStatus.IMPLEMENTED.value,
        "availability": AvailabilityStatus.INSTALLED.value,
        "input_types": [{"type": "environmental_raster_v1"}],
        "output_types": [{"type": "landscape_metric_summary_v1"}],
        "expected_evidence_types": ["mean_patch_size_ha", "landscape_division_index"],
        "preconditions": ["Categorical land-cover or continuous canopy height raster"],
        "scientific_assumptions": ["Spatial resolution is sufficient to detect habitat boundaries"],
        "default_parameters": {"neighborhood_connectivity": 8},
        "implementations": [
            {
                "implementation_key": "pylandstats_landscape_metrics_v1",
                "display_name": "PyLandStats Habitat Fragmentation Engine",
                "provider": "bais_landscape",
                "adapter_module": "src.adapters.landscape_metrics",
                "backend_environment": "local_worker",
                "runtime_version": "2.4.1",
                "availability": AvailabilityStatus.INSTALLED.value,
                "validation_status": KnowledgeStatus.IMPLEMENTED.value,
                "is_default": True,
            }
        ],
    },

    # ----------------------------------------------------
    # 12. ECOSYSTEM FUNCTION & BIOGEOCHEMISTRY
    # ----------------------------------------------------
    {
        "app_name": "bais_biodiversity_extensions",
        "capability_key": "estimate_primary_productivity_ndvi",
        "display_name": "Primary Productivity & NDVI Time-Series Extraction",
        "scientific_purpose": "Calculates integrated seasonal NDVI, gross primary productivity proxies, and phenological start-of-season metrics from multispectral rasters.",
        "domain": BiodiversityDomain.ECOSYSTEM_FUNCTION.value,
        "subdomain": "primary_productivity",
        "ebv_dimension": EBVDimension.ECOSYSTEM_FUNCTION.value,
        "capability_scope": CapabilityScope.OFFICIAL_EXTENSION.value,
        "is_generic": True,
        "scientific_maturity": ScientificMaturity.INSTALLED.value,
        "knowledge_status": KnowledgeStatus.IMPLEMENTED.value,
        "availability": AvailabilityStatus.INSTALLED.value,
        "input_types": [{"type": "multispectral_surface_reflectance_v1"}],
        "output_types": [{"type": "productivity_time_series_v1"}],
        "expected_evidence_types": ["integrated_annual_ndvi", "sos_phenology_day"],
        "preconditions": ["Surface reflectance rasters with Red and NIR bands"],
        "scientific_assumptions": ["NDVI relates monotonically to active photosynthetic biomass"],
        "default_parameters": {"cloud_masking": True},
        "implementations": [
            {
                "implementation_key": "rasterio_ndvi_productivity_v1",
                "display_name": "Rasterio Multispectral Productivity Analyzer",
                "provider": "bais_remote_sensing",
                "adapter_module": "src.adapters.ndvi_productivity",
                "backend_environment": "local_worker",
                "runtime_version": "1.3.9",
                "availability": AvailabilityStatus.INSTALLED.value,
                "validation_status": KnowledgeStatus.IMPLEMENTED.value,
                "is_default": True,
            }
        ],
    },

    # ----------------------------------------------------
    # 13. ENVIRONMENTAL DRIVERS & CLIMATE IMPACTS
    # ----------------------------------------------------
    {
        "app_name": "bais_core_platform",
        "capability_key": "model_climate_change_impacts",
        "display_name": "Future Climate Projection & Range Shift Analysis",
        "scientific_purpose": "Projects fitted species distribution models onto CMIP6 climate scenario rasters (SSP2-4.5, SSP5-8.5) to estimate prospective range contractions or expansions.",
        "domain": BiodiversityDomain.BIODIVERSITY_CHANGE_DRIVERS.value,
        "subdomain": "climate_change",
        "ebv_dimension": None,
        "capability_scope": CapabilityScope.GENERIC_CORE.value,
        "is_generic": True,
        "scientific_maturity": ScientificMaturity.INSTALLED.value,
        "knowledge_status": KnowledgeStatus.IMPLEMENTED.value,
        "availability": AvailabilityStatus.INSTALLED.value,
        "input_types": [{"type": "fitted_sdm_model_v1"}, {"type": "future_climate_raster_v1"}],
        "output_types": [{"type": "projected_suitability_raster_v1"}],
        "expected_evidence_types": ["percentage_suitable_area_change", "centroid_displacement_km"],
        "preconditions": ["Fitted SDM object", "Future climate scenario rasters in identical CRS"],
        "scientific_assumptions": ["Niche conservatism over projected timeframe"],
        "default_parameters": {"scenarios": ["ssp245", "ssp585"], "time_horizon": "2050"},
        "implementations": [
            {
                "implementation_key": "cmip6_projection_engine_v1",
                "display_name": "CMIP6 Bioclimatic Projection Adapter",
                "provider": "bais_climate",
                "adapter_module": "src.adapters.climate_projection",
                "backend_environment": "local_worker",
                "runtime_version": "1.0.0",
                "availability": AvailabilityStatus.INSTALLED.value,
                "validation_status": KnowledgeStatus.IMPLEMENTED.value,
                "is_default": True,
            }
        ],
    },

    # ----------------------------------------------------
    # 14. INVASIVE SPECIES & BIOSECURITY
    # ----------------------------------------------------
    {
        "app_name": "bais_biodiversity_extensions",
        "capability_key": "evaluate_invasion_risk",
        "display_name": "Invasion Front Velocity & Biosecurity Risk Assessment",
        "scientific_purpose": "Calculates radial expansion velocity and spatial overlap between invasive taxon occurrences and native protected areas.",
        "domain": BiodiversityDomain.INVASION_BIOLOGY.value,
        "subdomain": "range_expansion",
        "ebv_dimension": EBVDimension.SPECIES_POPULATIONS.value,
        "capability_scope": CapabilityScope.OFFICIAL_EXTENSION.value,
        "is_generic": True,
        "scientific_maturity": ScientificMaturity.INSTALLED.value,
        "knowledge_status": KnowledgeStatus.IMPLEMENTED.value,
        "availability": AvailabilityStatus.INSTALLED.value,
        "input_types": [{"type": "occurrence_dataset_v1"}],
        "output_types": [{"type": "invasion_risk_report_v1"}],
        "expected_evidence_types": ["invasion_front_velocity_km_yr", "native_taxa_overlap_km2"],
        "preconditions": ["Temporal occurrence records of invasive taxon", "Range polygons of native taxa"],
        "scientific_assumptions": ["Expansion modeled as radial diffusion process"],
        "default_parameters": {"time_intervals_years": 5},
        "implementations": [
            {
                "implementation_key": "invasion_velocity_calculator_v1",
                "display_name": "Invasion Diffusion & Velocity Calculator",
                "provider": "bais_biosecurity",
                "adapter_module": "src.adapters.invasion_calculator",
                "backend_environment": "local_worker",
                "runtime_version": "1.0.0",
                "availability": AvailabilityStatus.INSTALLED.value,
                "validation_status": KnowledgeStatus.IMPLEMENTED.value,
                "is_default": True,
            }
        ],
    },
]


def seed_biodiversity_taxonomy(session: Session) -> dict[str, int]:
    """
    Idempotently seeds ScientificApplications, canonical ScientificCapabilities,
    and their 1..N CapabilityImplementation records.
    Safe against reruns and updates existing records in place.
    """
    from src.models.scientific_capability import CapabilityImplementation

    app_map: dict[str, ScientificApplication] = {}
    apps_created = 0
    apps_updated = 0

    for app_data in SEED_APPLICATIONS:
        existing_app = session.query(ScientificApplication).filter_by(name=app_data["name"]).first()
        if existing_app:
            existing_app.display_name = app_data["display_name"]
            existing_app.category = app_data["category"]
            existing_app.description = app_data["description"]
            existing_app.host_environment = app_data["host_environment"]
            existing_app.invocation_type = app_data["invocation_type"]
            existing_app.is_gpu_required = app_data["is_gpu_required"]
            existing_app.is_enabled = app_data["is_enabled"]
            app_map[app_data["name"]] = existing_app
            apps_updated += 1
        else:
            new_app = ScientificApplication(**app_data)
            session.add(new_app)
            session.flush()
            app_map[app_data["name"]] = new_app
            apps_created += 1

    caps_created = 0
    caps_updated = 0
    impls_created = 0
    impls_updated = 0

    for cap_data in SEED_CAPABILITIES:
        app_name = cap_data["app_name"]
        app = app_map.get(app_name)
        if not app:
            continue

        impls_list = cap_data.get("implementations", [])
        cap_dict = {k: v for k, v in cap_data.items() if k not in ["app_name", "implementations"]}
        existing_cap = session.query(ScientificCapability).filter_by(capability_key=cap_dict["capability_key"]).first()

        if existing_cap:
            for key, val in cap_dict.items():
                setattr(existing_cap, key, val)
            existing_cap.application_id = app.id
            cap_obj = existing_cap
            caps_updated += 1
        else:
            cap_obj = ScientificCapability(application_id=app.id, **cap_dict)
            session.add(cap_obj)
            session.flush()
            caps_created += 1

        # Seed attached implementations
        for impl_item in impls_list:
            existing_impl = session.query(CapabilityImplementation).filter_by(
                implementation_key=impl_item["implementation_key"]
            ).first()
            if existing_impl:
                for ikey, ival in impl_item.items():
                    setattr(existing_impl, ikey, ival)
                existing_impl.scientific_capability_id = cap_obj.id
                impls_updated += 1
            else:
                new_impl = CapabilityImplementation(
                    scientific_capability_id=cap_obj.id,
                    **impl_item
                )
                session.add(new_impl)
                impls_created += 1

    session.commit()

    return {
        "apps_created": apps_created,
        "apps_updated": apps_updated,
        "capabilities_created": caps_created,
        "capabilities_updated": caps_updated,
        "implementations_created": impls_created,
        "implementations_updated": impls_updated,
        "total_capabilities": session.query(ScientificCapability).count(),
        "total_implementations": session.query(CapabilityImplementation).count(),
    }
