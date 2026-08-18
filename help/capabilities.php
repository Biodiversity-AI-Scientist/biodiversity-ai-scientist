<?php

declare(strict_types=1);

$activeTopic = 'capabilities';
$pageTitle = 'Scientific Capabilities, Two-Tier Decoupling & 4-Tier Scopes — AI Scientist Help';

require_once __DIR__ . '/includes/help_header.php';

?>

<div class="row mb-4">
    <div class="col-12">
        <div class="d-flex align-items-center gap-2 mb-1">
            <span class="badge bg-primary text-white text-uppercase tracking-wide">Tools &amp; Capabilities</span>
            <h1 class="h3 mb-0 fw-bold">Scientific Capability Registry, Two-Tier Decoupling &amp; Scope Architecture</h1>
        </div>
        <p class="text-muted mb-0">
            Authoritative guide to grounded scientific software, two-tier method vs implementation decoupling, 14 standardized biodiversity domains, 4-tier implementation scope governance, and machine-validatable semantic contracts.
        </p>
    </div>
</div>

<div class="row g-4">
    <div class="col-lg-8">
        <!-- Two-Tier Architecture -->
        <div class="card shadow-sm border-0 mb-4">
            <div class="card-header bg-white py-3 border-start border-4 border-success">
                <h5 class="fw-bold text-dark mb-0"><i class="bi bi-diagram-3 text-success me-2"></i>Two-Tier Physical Architecture (1:N Binding)</h5>
            </div>
            <div class="card-body p-4">
                <p class="text-secondary mb-3">
                    BAIS physically decouples abstract scientific domain methods from concrete software execution bindings:
                </p>
                <div class="row g-3 mb-2">
                    <div class="col-md-6">
                        <div class="p-3 bg-light rounded border h-100">
                            <div class="fw-bold text-primary mb-1">Tier 1: ScientificCapability</div>
                            <p class="small text-muted mb-0">
                                Abstract scientific method (e.g. <code>extract_image_embeddings</code>), domain assignment, scientific assumptions, precondition rules, input/output semantic data contracts, and flag <code>is_generic</code>. Free from vendor or server deployment keys.
                            </p>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="p-3 bg-light rounded border h-100">
                            <div class="fw-bold text-success mb-1">Tier 2: CapabilityImplementation</div>
                            <p class="small text-muted mb-0">
                                Concrete software adapter bindings (1:N foreign key), provider, execution module, backend runtime (e.g. CUDA GPU worker vs local host), runtime version, and implementation-level scope.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Implementation-Level 4-Tier Scope Governance -->
        <div class="card shadow-sm border-0 mb-4">
            <div class="card-header bg-white py-3 border-start border-4 border-primary">
                <h5 class="fw-bold text-dark mb-0"><i class="bi bi-tags-fill text-primary me-2"></i>Implementation-Level 4-Tier Scope Governance</h5>
            </div>
            <div class="card-body p-4">
                <p class="text-secondary mb-3">
                    To prevent conflating universal biological methods with private laboratory infrastructure, BAIS governs deployment scopes at the implementation adapter level:
                </p>

                <div class="row g-3 mb-2">
                    <div class="col-md-6">
                        <div class="p-3 bg-light rounded border h-100">
                            <div class="d-flex align-items-center gap-2 mb-1">
                                <span class="badge bg-primary">Generic Core</span>
                                <code class="small text-muted">generic_core</code>
                            </div>
                            <p class="small text-muted mb-0">Standardized, lightweight biodiversity and statistical algorithms built into the base platform without private proprietary dependencies (e.g. Darwin Core validation, Alpha/Beta diversity, EOO/AOO hulls).</p>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="p-3 bg-light rounded border h-100">
                            <div class="d-flex align-items-center gap-2 mb-1">
                                <span class="badge bg-success">Deployment Specific</span>
                                <code class="small text-muted">deployment_specific</code>
                            </div>
                            <p class="small text-muted mb-0">Private laboratory pipelines bound to dedicated GPU workers, specimen photographic archives, or proprietary segmentation tools (e.g. <code>specialized_dinov3_v1</code>).</p>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="p-3 bg-light rounded border h-100">
                            <div class="d-flex align-items-center gap-2 mb-1">
                                <span class="badge text-white" style="background-color: #6f42c1;">Official Extension</span>
                                <code class="small text-muted">official_extension</code>
                            </div>
                            <p class="small text-muted mb-0">Audited extensions provided by the core AI Scientist platform (e.g. advanced remote sensing plugins, climate layer extractors).</p>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="p-3 bg-light rounded border h-100">
                            <div class="d-flex align-items-center gap-2 mb-1">
                                <span class="badge bg-warning text-dark">Third-Party Community</span>
                                <code class="small text-muted">third_party_community</code>
                            </div>
                            <p class="small text-muted mb-0">User-contributed adapters, external API connectors, and community Python scientific routines.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Capability Selection Engine -->
        <div class="card shadow-sm border-0 mb-4">
            <div class="card-header bg-white py-3 border-start border-4 border-info">
                <h5 class="fw-bold text-dark mb-0"><i class="bi bi-cpu text-primary me-2"></i>Deterministic-First Selection Engine &amp; Usable Paths</h5>
            </div>
            <div class="card-body p-4">
                <div class="table-responsive mb-3">
                    <table class="table table-bordered table-sm align-middle spec-table">
                        <thead class="table-light">
                            <tr>
                                <th>Candidates Found</th>
                                <th>Resolution Strategy</th>
                                <th>Outcome &amp; Provenance</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td class="fw-bold text-danger">0 Usable Execution Paths</td>
                                <td>No Usable Path</td>
                                <td>Automatically logs a <code>CapabilityGap</code>; flags investigation step as <code>capability_blocked</code>.</td>
                            </tr>
                            <tr>
                                <td class="fw-bold text-success">Exactly 1 Usable Option</td>
                                <td>Deterministic Sole-Option</td>
                                <td>Assigns tool with deterministic rationale; bypasses LLM latency and cost.</td>
                            </tr>
                            <tr>
                                <td class="fw-bold text-primary">&gt;1 Eligible Tools</td>
                                <td>LLM Tradeoff Selection</td>
                                <td>Invokes LLM to evaluate accuracy/cost trade-offs and logs rejected alternatives.</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <h6 class="fw-bold text-dark mb-2"><i class="bi bi-exclamation-octagon text-danger me-2"></i>Capability Gaps &amp; Status Lifecycle</h6>
                <p class="small text-muted mb-0">
                    A capability gap occurs when an investigation plan requires a method with <strong>zero usable physical implementations</strong> (neither locally installed nor configured external tool). Gaps follow a governed lifecycle (<code>unresolved</code> &rarr; <code>in_progress</code> &rarr; <code>resolved</code> / <code>waived</code>).
                </p>
            </div>
        </div>

        <!-- 14 Standardized Biodiversity Research Domains -->
        <div class="card shadow-sm border-0 mb-4">
            <div class="card-header bg-white py-3">
                <h5 class="fw-bold text-dark mb-0"><i class="bi bi-globe2 text-success me-2"></i>14 Standardized Biodiversity Research Domains</h5>
            </div>
            <div class="card-body p-4">
                <div class="row g-2 small">
                    <div class="col-md-6">1. <strong>Biodiversity Informatics &amp; Data Quality:</strong> WoRMS, DwC quality</div>
                    <div class="col-md-6">2. <strong>Taxonomy &amp; Nomenclature:</strong> Species delimitation, synonymy</div>
                    <div class="col-md-6">3. <strong>Species Populations &amp; Occurrence:</strong> Occurrence aggregation, trends</div>
                    <div class="col-md-6">4. <strong>Species Traits &amp; Morphology:</strong> Morphometrics, DINOv3 vision</div>
                    <div class="col-md-6">5. <strong>Genetic Composition &amp; Diversity:</strong> Population differentiation, Fst</div>
                    <div class="col-md-6">6. <strong>Community Ecology &amp; Interaction Networks:</strong> Diversity, bipartite graphs</div>
                    <div class="col-md-6">7. <strong>Phylogenetics &amp; Evolutionary Dynamics:</strong> IQ-TREE 2 ML inference</div>
                    <div class="col-md-6">8. <strong>Biogeography &amp; Macroecology:</strong> EOO/AOO range metrics, MaxEnt SDM</div>
                    <div class="col-md-6">9. <strong>Conservation Status &amp; Red List Governance:</strong> IUCN Criterion B</div>
                    <div class="col-md-6">10. <strong>eDNA &amp; Environmental Genomics:</strong> DADA2 metabarcoding, ASVs</div>
                    <div class="col-md-6">11. <strong>Ecosystem Structure &amp; Biomes:</strong> Canopy height, fragmentation</div>
                    <div class="col-md-6">12. <strong>Ecosystem Function &amp; Biogeochemistry:</strong> NDVI phenology, productivity</div>
                    <div class="col-md-6">13. <strong>Environmental Drivers &amp; Climate Impacts:</strong> CMIP6 climate shifts</div>
                    <div class="col-md-6">14. <strong>Invasive Species &amp; Biosecurity:</strong> Diffusion velocity, native overlap</div>
                </div>
            </div>
        </div>
    </div>

    <div class="col-lg-4">
        <!-- Canonical Semantic Data Types -->
        <div class="card shadow-sm border-0 mb-4">
            <div class="card-header bg-white py-3">
                <h6 class="fw-bold text-dark mb-0"><i class="bi bi-file-earmark-code me-2"></i>Canonical Semantic Contracts (14 Types)</h6>
            </div>
            <div class="card-body p-3">
                <ul class="small text-secondary ps-3 mb-0">
                    <li class="mb-2"><code>occurrence_dataset_v1</code> — DwC tabular records (<code>occurrence_id</code>).</li>
                    <li class="mb-2"><code>specimen_image_collection_v1</code> — Specimen photo collection (<code>image_id</code>).</li>
                    <li class="mb-2"><code>dense_feature_embedding_v1</code> — Intermediate Result/Artifact (<code>entity_id</code>).</li>
                    <li class="mb-2"><code>taxonomic_backbone_v1</code> — Standard Linnaean hierarchy (<code>taxon_id</code>).</li>
                    <li class="mb-2"><code>morphological_trait_table_v1</code> — Long trait matrix (<code>trait_observation_id</code>).</li>
                    <li class="mb-2"><code>range_polygon_manifest_v1</code> — GeoJSON range polygons (<code>taxon_id</code>, EPSG:4326).</li>
                    <li class="mb-2"><code>phylogenetic_tree_v1</code> — Newick tree dataset (<code>tree_id</code>).</li>
                    <li class="mb-2"><code>community_abundance_matrix_v1</code> — Site &times; Species matrix (<code>matrix_id</code>).</li>
                    <li class="mb-2"><code>genetic_distance_matrix_v1</code> — Pairwise distance matrix (<code>matrix_id</code>).</li>
                    <li class="mb-2"><code>population_time_series_v1</code> — Temporal trend series (<code>observation_id</code>).</li>
                    <li class="mb-2"><code>environmental_raster_v1</code> — Spatial raster layer (<code>raster_layer_id</code>).</li>
                    <li class="mb-2"><code>asv_table_v1</code> — eDNA amplicon read table (<code>asv_id</code>).</li>
                    <li class="mb-2"><code>interaction_network_v1</code> — Ecological interaction graph (<code>network_id</code>).</li>
                    <li class="mb-2"><code>spatial_metric_result_v1</code> — EOO/AOO assessment result (<code>metric_id</code>).</li>
                </ul>
            </div>
        </div>

        <!-- Scientific Maturity & Usability -->
        <div class="card shadow-sm border-0 mb-4">
            <div class="card-header bg-white py-3">
                <h6 class="fw-bold text-dark mb-0"><i class="bi bi-award-fill text-warning me-2"></i>Execution Usability States</h6>
            </div>
            <div class="card-body p-3">
                <div class="d-flex flex-column gap-2 small">
                    <div class="d-flex justify-content-between">
                        <span class="badge bg-success">installed</span>
                        <span class="text-muted">Locally operational</span>
                    </div>
                    <div class="d-flex justify-content-between">
                        <span class="badge bg-warning text-dark">external</span>
                        <span class="text-muted">External tool usable path</span>
                    </div>
                    <div class="d-flex justify-content-between">
                        <span class="badge bg-info text-dark">validated</span>
                        <span class="text-muted">Benchmark verified</span>
                    </div>
                    <div class="d-flex justify-content-between">
                        <span class="badge bg-secondary">not_installed</span>
                        <span class="text-muted">Requires gap resolution</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<?php require_once __DIR__ . '/includes/help_footer.php'; ?>

