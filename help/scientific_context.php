<?php

declare(strict_types=1);

$activeTopic = 'scientific_context';
$pageTitle = 'Phase 7: Scientific Context Engine — AI Scientist Help';

require_once __DIR__ . '/includes/help_header.php';

?>

<div class="row mb-4">
    <div class="col-12">
        <div class="d-flex align-items-center gap-2 mb-1">
            <span class="badge bg-success text-white text-uppercase tracking-wide">Phase 7 Architecture</span>
            <h1 class="h3 mb-0 fw-bold">Scientific Context Engine &amp; Provenance Segregation</h1>
        </div>
        <p class="text-muted mb-0">
            Unified multi-component context assembly ensuring all LLM reasoning is strictly grounded in database world models and empirical DWH records with clear provenance tagging.
        </p>
    </div>
</div>

<div class="row g-4">
    <div class="col-lg-8">
        <div class="card shadow-sm border-0 mb-4">
            <div class="card-header bg-white py-3">
                <h5 class="fw-bold text-dark mb-0"><i class="bi bi-intersect text-primary me-2"></i>Context Types &amp; Assembly Contracts</h5>
            </div>
            <div class="card-body p-4">
                <p>
                    The <code>ScientificContextService</code> aggregates distributed database records into strongly-typed Pydantic context packets before sending requests to the LLM Gateway:
                </p>

                <div class="table-responsive mb-4">
                    <table class="table table-bordered table-sm align-middle spec-table">
                        <thead>
                            <tr>
                                <th>Context Schema</th>
                                <th>Target Scientific Stage</th>
                                <th>Key Components Assembled</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td class="fw-bold"><code>InvestigationPlanningContext</code></td>
                                <td>Phase 8 DAG Generation</td>
                                <td>Approved ResearchPlan, focal question, datasets, empirical constraints, previous results, missing information.</td>
                            </tr>
                            <tr>
                                <td class="fw-bold"><code>CapabilityMatchingContext</code></td>
                                <td>Phase 9 Tool Selection</td>
                                <td>Target step goal, candidate capabilities from registry, required input/output MIME types.</td>
                            </tr>
                            <tr>
                                <td class="fw-bold"><code>ExperimentPlanningContext</code></td>
                                <td>Phase 10 Analysis Spec</td>
                                <td>Bound investigation step, selected capability metadata, dataset versions, parameter schemas.</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <h6 class="fw-bold text-dark mb-2"><i class="bi bi-tag-fill text-primary me-2"></i>Explicit Provenance Tagging Syntax</h6>
                <p class="small text-muted mb-2">
                    To prevent LLM hallucination and ungrounded data fabrication, every rendered prompt section is tagged with its authoritative source:
                </p>

                <div class="code-snippet mb-0">
<span class="text-success">[FACT]</span> Project #1: "Phylogeography of Nassarius kraussianus"
<span class="text-info">[RESEARCH PLAN]</span> Plan #4 (v2, Status: APPROVED): Core Objective: "Test morphological divergence..."
<span class="text-warning">[GBIF_DWH_OCCURRENCE]</span> 1,248 specimen records in Saldanha Bay vs Algoa Bay
<span class="text-danger">[MISSING INFO]</span> No nuclear gene sequences currently ingested in database
<span class="text-primary">[PROVENANCE: DATABASE_WORLD_MODEL]</span> Entity: ResearchQuestion #12
                </div>
            </div>
        </div>
    </div>

    <div class="col-lg-4">
        <div class="card shadow-sm border-0 mb-4">
            <div class="card-header bg-white py-3">
                <h6 class="fw-bold text-dark mb-0"><i class="bi bi-speedometer2 me-2"></i>Performance &amp; Budgets</h6>
            </div>
            <div class="card-body p-3">
                <p class="small text-muted mb-2">
                    Every context assembly computes strict execution metrics recorded in <code>ContextBuildMetadata</code>:
                </p>
                <ul class="small text-secondary ps-3 mb-0">
                    <li><strong>Assembly Latency:</strong> Wall-clock database aggregation time in milliseconds.</li>
                    <li><strong>Rendered Char Count:</strong> Precise character length of prompt context.</li>
                    <li><strong>Entity Counts:</strong> Quantified count of datasets, steps, hypotheses, and constraints.</li>
                </ul>
            </div>
        </div>
    </div>
</div>

<?php require_once __DIR__ . '/includes/help_footer.php'; ?>
