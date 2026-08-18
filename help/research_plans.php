<?php

declare(strict_types=1);

$activeTopic = 'research_plans';
$pageTitle = 'Phase 6: Research Plans Specification — AI Scientist Help';

require_once __DIR__ . '/includes/help_header.php';

?>

<div class="row mb-4">
    <div class="col-12">
        <div class="d-flex align-items-center gap-2 mb-1">
            <span class="badge bg-info text-dark text-uppercase tracking-wide">Phase 6 Specification</span>
            <h1 class="h3 mb-0 fw-bold">Research Plans: Specification, Governance &amp; Lifecycle</h1>
        </div>
        <p class="text-muted mb-0">
            Formal scientific research strategies bridging high-level project objectives into explicit analytical stages, required evidence, and validation criteria.
        </p>
    </div>
</div>

<div class="row g-4">
    <div class="col-lg-8">
        <div class="card shadow-sm border-0 mb-4">
            <div class="card-header bg-white py-3">
                <h5 class="fw-bold text-dark mb-0"><i class="bi bi-file-earmark-text text-primary me-2"></i>Structured 7-Section Scientific Plan Schema</h5>
            </div>
            <div class="card-body p-4">
                <p>
                    Every <code>ResearchPlan</code> record in the scientific world model is defined by 7 mandatory structural fields designed for scientific rigor:
                </p>

                <div class="table-responsive mb-4">
                    <table class="table table-bordered table-sm align-middle spec-table">
                        <thead>
                            <tr>
                                <th style="width: 25%;">Section / Field</th>
                                <th>Scientific Purpose &amp; Contract</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td class="fw-bold">1. Title &amp; Objective</td>
                                <td>Clear, testable formulation of the central scientific aim for the project.</td>
                            </tr>
                            <tr>
                                <td class="fw-bold">2. Scientific Background</td>
                                <td>Theoretical rationale, literature context, and biological domain foundation.</td>
                            </tr>
                            <tr>
                                <td class="fw-bold">3. Proposed Strategy</td>
                                <td>Methodological framework (e.g. comparative morphometrics, self-supervised representation extraction, statistical significance testing).</td>
                            </tr>
                            <tr>
                                <td class="fw-bold">4. Evidence Required</td>
                                <td>JSON list of empirical artifacts required to validate or refute hypotheses (e.g. <em>"WoRMS verified species matrix"</em>, <em>"DINOv3 silhouette separation score > 0.65"</em>).</td>
                            </tr>
                            <tr>
                                <td class="fw-bold">5. Analytical Stages</td>
                                <td>Ordered sequence of analytical phases stored in <code>research_plan_stages</code> or JSON stage definitions.</td>
                            </tr>
                            <tr>
                                <td class="fw-bold">6. Validation Strategy</td>
                                <td>Quantitative controls, train/test split protocols, out-of-distribution robustness tests, and cross-validation schemas.</td>
                            </tr>
                            <tr>
                                <td class="fw-bold">7. Interpretation Criteria</td>
                                <td>Decision thresholds specifying how observed empirical outcomes map to biological conclusions.</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <h6 class="fw-bold text-dark mb-2"><i class="bi bi-arrow-repeat text-success me-2"></i>Versioning &amp; Approval Governance</h6>
                <p class="small text-muted mb-0">
                    Research plans support iterative refinement. Modifying an approved plan increments the plan's <code>version</code> number and marks previous versions as superseded. An approved plan serves as the primary grounding context for Phase 8 <strong>Investigation Planning (DAG)</strong>.
                </p>
            </div>
        </div>
    </div>

    <div class="col-lg-4">
        <div class="card shadow-sm border-0 mb-4">
            <div class="card-header bg-white py-3">
                <h6 class="fw-bold text-dark mb-0"><i class="bi bi-shield-check me-2"></i>Lifecycle Status States</h6>
            </div>
            <div class="card-body p-3">
                <ul class="list-group list-group-flush small">
                    <li class="list-group-item d-flex justify-content-between align-items-center px-0">
                        <span><span class="badge bg-secondary me-2">draft</span> Initial formulation</span>
                    </li>
                    <li class="list-group-item d-flex justify-content-between align-items-center px-0">
                        <span><span class="badge bg-warning text-dark me-2">under_review</span> Under researcher review</span>
                    </li>
                    <li class="list-group-item d-flex justify-content-between align-items-center px-0">
                        <span><span class="badge bg-success me-2">approved</span> Validated &amp; ready for DAG</span>
                    </li>
                    <li class="list-group-item d-flex justify-content-between align-items-center px-0">
                        <span><span class="badge bg-danger me-2">rejected</span> Rejected / Superseded</span>
                    </li>
                </ul>
            </div>
        </div>
    </div>
</div>

<?php require_once __DIR__ . '/includes/help_footer.php'; ?>
