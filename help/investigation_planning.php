<?php

declare(strict_types=1);

$activeTopic = 'investigation_planning';
$pageTitle = 'Phase 8: Investigation DAGs & Step Sequencing — AI Scientist Help';

require_once __DIR__ . '/includes/help_header.php';

?>

<div class="row mb-4">
    <div class="col-12">
        <div class="d-flex align-items-center gap-2 mb-1">
            <span class="badge bg-primary text-white text-uppercase tracking-wide">Phase 8 Architecture</span>
            <h1 class="h3 mb-0 fw-bold">Investigation Planning: Directed Acyclic Graphs (DAG) &amp; Step Sequencing</h1>
        </div>
        <p class="text-muted mb-0">
            Decomposing research questions and approved plans into an explicit, non-prescriptive dependency graph of executable InvestigationSteps.
        </p>
    </div>
</div>

<div class="row g-4">
    <div class="col-lg-8">
        <div class="card shadow-sm border-0 mb-4">
            <div class="card-header bg-white py-3">
                <h5 class="fw-bold text-dark mb-0"><i class="bi bi-diagram-2 text-primary me-2"></i>Graph Architecture &amp; Entities</h5>
            </div>
            <div class="card-body p-4">
                <p>
                    Rather than generating flat task lists or executing hard-coded linear scripts, Phase 8 decomposes a scientific question into an explicit <strong>Directed Acyclic Graph (DAG)</strong>:
                </p>

                <div class="table-responsive mb-4">
                    <table class="table table-bordered table-sm align-middle spec-table">
                        <thead>
                            <tr>
                                <th>Relational Entity</th>
                                <th>Role in Scientific World Model</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td class="fw-bold"><code>InvestigationPlanGeneration</code></td>
                                <td>Tracks the prompt invocation, summary rationale, identified uncertainties, and LLM model provenance for an investigation graph generation attempt.</td>
                            </tr>
                            <tr>
                                <td class="fw-bold"><code>InvestigationStep</code></td>
                                <td>Atomic scientific unit with title, scientific goal, rationale, extensible <code>step_type</code> (e.g. <em>taxonomy, representation, model_training, statistical_analysis, robustness, evidence_synthesis</em>), expected evidence, and completion criteria.</td>
                            </tr>
                            <tr>
                                <td class="fw-bold"><code>InvestigationStepDependency</code></td>
                                <td>Relational prerequisite edge linking a dependent step to its required prerequisite step (<code>step_id &rarr; depends_on_step_id</code>).</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <h6 class="fw-bold text-dark mb-2"><i class="bi bi-shuffle text-success me-2"></i>Kahn's Topological Sorting &amp; Cycle Prevention</h6>
                <p class="small text-muted mb-3">
                    The backend executes Kahn's algorithm over all dependency records to compute valid linear execution orders, identify parallelizable execution tiers, and prevent circular dependency deadlocks.
                </p>

                <div class="p-3 bg-light rounded border">
                    <h6 class="fw-bold text-dark mb-1"><i class="bi bi-shield-lock text-warning me-2"></i>Multi-Factor Readiness Computation</h6>
                    <p class="small text-muted mb-0">
                        A step's readiness is evaluated dynamically by <code>compute_step_readiness()</code>. A step is <code>ready</code> only when all prerequisite steps in the DAG have status <code>completed</code> AND its capability requirements are satisfied. If prerequisites are pending, state is <code>dependency_blocked</code>; if no tool exists, state is <code>capability_blocked</code>.
                    </p>
                </div>
            </div>
        </div>
    </div>

    <div class="col-lg-4">
        <div class="card shadow-sm border-0 mb-4">
            <div class="card-header bg-white py-3">
                <h6 class="fw-bold text-dark mb-0"><i class="bi bi-layers me-2"></i>Step Type Taxonomy</h6>
            </div>
            <div class="card-body p-3">
                <p class="small text-muted mb-2">
                    Standard step types defined in the extensible taxonomy:
                </p>
                <ul class="small text-secondary ps-3 mb-0">
                    <li><code>data_assessment</code>: Data audit &amp; filtering</li>
                    <li><code>taxonomy</code>: Taxon name / WoRMS validation</li>
                    <li><code>representation</code>: Feature &amp; embedding extraction</li>
                    <li><code>model_training</code>: Supervised model training</li>
                    <li><code>statistical_analysis</code>: Hypothesis significance testing</li>
                    <li><code>robustness</code>: Cross-validation / Out-of-distribution</li>
                    <li><code>evidence_synthesis</code>: Tri-grounded synthesis</li>
                    <li><code>expert_review</code>: Researcher verification</li>
                </ul>
            </div>
        </div>
    </div>
</div>

<?php require_once __DIR__ . '/includes/help_footer.php'; ?>
