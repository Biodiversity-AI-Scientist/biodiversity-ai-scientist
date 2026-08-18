<?php

declare(strict_types=1);

$activeTopic = 'technical_reference';
$pageTitle = 'Technical & Schema Reference — AI Scientist Help';

require_once __DIR__ . '/includes/help_header.php';

?>

<div class="row mb-4">
    <div class="col-12">
        <div class="d-flex align-items-center gap-2 mb-1">
            <span class="badge bg-dark text-white text-uppercase tracking-wide">Developer &amp; Database Specs</span>
            <h1 class="h3 mb-0 fw-bold">Technical Reference: Schemas, Foreign Keys &amp; REST APIs</h1>
        </div>
        <p class="text-muted mb-0">
            Exhaustive database entity relationship reference and FastAPI endpoint specifications.
        </p>
    </div>
</div>

<!-- Section 1: Relational Schemas -->
<div class="card shadow-sm border-0 mb-4">
    <div class="card-header bg-white py-3">
        <h5 class="fw-bold text-dark mb-0"><i class="bi bi-database text-primary me-2"></i>Relational Database World Model (MySQL)</h5>
    </div>
    <div class="card-body p-4">
        <p class="text-secondary small mb-3">
            All tables are created and versioned through Alembic migrations (SQLAlchemy ORM models in <code>src/models/</code>):
        </p>

        <div class="table-responsive">
            <table class="table table-bordered table-sm align-middle spec-table small">
                <thead>
                    <tr>
                        <th style="width: 22%;">Table Name</th>
                        <th style="width: 25%;">Primary &amp; Foreign Keys</th>
                        <th>Core Columns &amp; Purpose</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><code>research_projects</code></td>
                        <td><code>id</code> (PK)</td>
                        <td><code>title</code>, <code>description</code>, <code>objective</code>, <code>domain</code>, <code>status</code>.</td>
                    </tr>
                    <tr>
                        <td><code>research_questions</code></td>
                        <td><code>id</code> (PK), <code>project_id</code> (FK)</td>
                        <td><code>question</code>, <code>priority</code>, <code>status</code>.</td>
                    </tr>
                    <tr>
                        <td><code>hypotheses</code></td>
                        <td><code>id</code> (PK), <code>question_id</code> (FK)</td>
                        <td><code>statement</code>, <code>rationale</code>, <code>status</code>.</td>
                    </tr>
                    <tr>
                        <td><code>dataset_versions</code></td>
                        <td><code>id</code> (PK), <code>project_id</code> (FK)</td>
                        <td><code>version_label</code>, <code>source_type</code>, <code>record_count</code>, <code>filter_criteria</code>.</td>
                    </tr>
                    <tr>
                        <td><code>research_plans</code></td>
                        <td><code>id</code> (PK), <code>project_id</code> (FK), <code>superseded_by_plan_id</code> (FK)</td>
                        <td><code>version</code>, <code>title</code>, <code>objective</code>, <code>scientific_background</code>, <code>proposed_strategy</code>, <code>evidence_required</code>, <code>analytical_stages</code>, <code>validation_strategy</code>, <code>interpretation_criteria</code>, <code>status</code>.</td>
                    </tr>
                    <tr>
                        <td><code>investigation_plan_generations</code></td>
                        <td><code>id</code> (PK), <code>question_id</code> (FK), <code>research_plan_id</code> (FK)</td>
                        <td><code>summary_rationale</code>, <code>identified_uncertainties</code>, <code>context_summary</code>, <code>model_provenance</code>.</td>
                    </tr>
                    <tr>
                        <td><code>investigation_steps</code></td>
                        <td><code>id</code> (PK), <code>project_id</code> (FK), <code>question_id</code> (FK), <code>generation_id</code> (FK)</td>
                        <td><code>title</code>, <code>scientific_goal</code>, <code>rationale</code>, <code>step_type</code>, <code>requires_capability</code>, <code>requires_experiment</code>, <code>required_operation</code>, <code>expected_evidence</code>, <code>completion_criteria</code>, <code>status</code>, <code>display_order</code>.</td>
                    </tr>
                    <tr>
                        <td><code>investigation_step_dependencies</code></td>
                        <td><code>id</code> (PK), <code>step_id</code> (FK), <code>depends_on_step_id</code> (FK)</td>
                        <td>Relational prerequisite edges for DAG sequencing.</td>
                    </tr>
                    <tr>
                        <td><code>scientific_applications</code></td>
                        <td><code>id</code> (PK)</td>
                        <td><code>name</code>, <code>display_name</code>, <code>category</code>, <code>host_environment</code>, <code>invocation_type</code>, <code>is_gpu_required</code>, <code>is_enabled</code>.</td>
                    </tr>
                    <tr>
                        <td><code>scientific_capabilities</code></td>
                        <td><code>id</code> (PK), <code>application_id</code> (FK)</td>
                        <td><code>capability_key</code>, <code>display_name</code>, <code>scientific_purpose</code>, <code>domain</code>, <code>subdomain</code>, <code>ebv_dimension</code>, <code>is_generic</code>, <code>scientific_maturity</code>, <code>expected_evidence_types</code>, <code>input_types</code>, <code>output_types</code>.</td>
                    </tr>
                    <tr>
                        <td><code>capability_implementation</code></td>
                        <td><code>id</code> (PK), <code>scientific_capability_id</code> (FK)</td>
                        <td><code>implementation_key</code>, <code>display_name</code>, <code>provider</code>, <code>adapter_module</code>, <code>backend_environment</code>, <code>runtime_version</code>, <code>implementation_scope</code> (<code>generic_core</code>, <code>official_extension</code>, <code>external_tool</code>, <code>identifyshell_specific</code>), <code>availability</code>, <code>validation_status</code>, <code>is_default</code>, <code>execution_parameters</code>.</td>
                    </tr>
                    <tr>
                        <td><code>capability_selections</code></td>
                        <td><code>id</code> (PK), <code>investigation_step_id</code> (FK), <code>selected_capability_id</code> (FK)</td>
                        <td><code>selection_method</code>, <code>scientific_rationale</code>, <code>rejected_alternatives</code>, <code>known_limitations</code>, <code>researcher_status</code>, <code>llm_provenance</code>.</td>
                    </tr>
                    <tr>
                        <td><code>capability_gaps</code></td>
                        <td><code>id</code> (PK), <code>project_id</code> (FK), <code>investigation_step_id</code> (FK)</td>
                        <td><code>scientific_requirement</code>, <code>rationale</code>, <code>identified_at</code>, <code>status</code> (<code>unresolved</code>, <code>in_progress</code>, <code>resolved</code>, <code>waived</code>), <code>resolved_at</code>, <code>resolution_notes</code>.</td>
                    </tr>
                    <tr>
                        <td><code>analysis_plan</code> <em>(Canonical: Experiment)</em></td>
                        <td><code>id</code> (PK), <code>question_id</code> (FK), <code>dataset_version_id</code> (FK)</td>
                        <td><code>method</code>, <code>estimand</code>, <code>assumptions</code>, <code>parameters</code> (JSON), <code>exploratory</code>, <code>status</code>.</td>
                    </tr>
                    <tr>
                        <td><code>analysis_run</code> <em>(Canonical: ExperimentRun)</em></td>
                        <td><code>id</code> (PK), <code>analysis_plan_id</code> (FK), <code>dataset_version_id</code> (FK)</td>
                        <td><code>status</code> (<code>pending</code>, <code>running</code>, <code>completed</code>, <code>failed</code>), <code>started_at</code>, <code>completed_at</code>, <code>parameters</code>, <code>execution_metadata</code>.</td>
                    </tr>
                    <tr>
                        <td><code>result</code></td>
                        <td><code>id</code> (PK), <code>analysis_run_id</code> (FK)</td>
                        <td><code>result_type</code>, <code>summary</code>, <code>payload</code> (JSON), <code>created_at</code>.</td>
                    </tr>
                    <tr>
                        <td><code>artifact</code></td>
                        <td><code>id</code> (PK), <code>project_id</code> (FK), <code>analysis_run_id</code> (FK)</td>
                        <td><code>artifact_type</code>, <code>uri</code>, <code>sha256</code> (cryptographic digest), <code>mime_type</code>, <code>size_bytes</code>.</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</div>

<!-- Section 2: Core REST API Endpoints -->
<div class="card shadow-sm border-0 mb-4">
    <div class="card-header bg-white py-3">
        <h5 class="fw-bold text-dark mb-0"><i class="bi bi-hdd-network text-primary me-2"></i>FastAPI REST Endpoints (Port 8000)</h5>
    </div>
    <div class="card-body p-4">
        <div class="table-responsive">
            <table class="table table-bordered table-sm align-middle spec-table small">
                <thead>
                    <tr>
                        <th style="width: 12%;">Method</th>
                        <th style="width: 38%;">Endpoint Path</th>
                        <th>Functionality &amp; Service Layer</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- Canonical Experiments (Phase 10 & 10A) -->
                    <tr class="table-light">
                        <td colspan="3" class="fw-bold text-primary"><i class="bi bi-flask-fill me-1"></i> Canonical Experiments &amp; Experiment Runs (Phase 10 / 10A)</td>
                    </tr>
                    <tr>
                        <td><span class="badge bg-primary">POST</span></td>
                        <td><code>/experiments</code></td>
                        <td>Creates a canonical Experiment protocol with pre-specified parameters.</td>
                    </tr>
                    <tr>
                        <td><span class="badge bg-success">GET</span></td>
                        <td><code>/experiments/{id}</code></td>
                        <td>Retrieves an Experiment specification and its linked runs.</td>
                    </tr>
                    <tr>
                        <td><span class="badge bg-primary">POST</span></td>
                        <td><code>/experiment-runs/{id}/execute</code></td>
                        <td>Dispatches deterministic experiment execution via modular providers or GPU backend.</td>
                    </tr>
                    <tr>
                        <td><span class="badge bg-success">GET</span></td>
                        <td><code>/experiment-runs/{id}/results</code></td>
                        <td>Returns structured Result records and verified Artifacts (with SHA-256).</td>
                    </tr>

                    <!-- Capabilities & 14 Domains (Phase 9 & B01) -->
                    <tr class="table-light">
                        <td colspan="3" class="fw-bold text-success"><i class="bi bi-tools me-1"></i> Capabilities, 4-Tier Scopes &amp; 14 Domains (Phase 9 &amp; B01)</td>
                    </tr>
                    <tr>
                        <td><span class="badge bg-success">GET</span></td>
                        <td><code>/capabilities/domains</code></td>
                        <td>Returns the 14 standardized biodiversity domains and capability count breakdowns.</td>
                    </tr>
                    <tr>
                        <td><span class="badge bg-success">GET</span></td>
                        <td><code>/capabilities/semantic-types</code></td>
                        <td>Returns the catalogue of standardized scientific input/output data types.</td>
                    </tr>
                    <tr>
                        <td><span class="badge bg-primary">POST</span></td>
                        <td><code>/capabilities/seed-taxonomy</code></td>
                        <td>Idempotently populates the database with standard biodiversity &amp; IdentifyShell capabilities.</td>
                    </tr>
                    <tr>
                        <td><span class="badge bg-success">GET</span></td>
                        <td><code>/capabilities?scope={scope}&amp;domain={domain}</code></td>
                        <td>Filters capabilities by 4-tier scope (<code>generic_core</code>, <code>identifyshell_specific</code>, etc.) and domain.</td>
                    </tr>
                    <tr>
                        <td><span class="badge bg-primary">POST</span></td>
                        <td><code>/investigation-steps/{id}/capability-selection/match</code></td>
                        <td>Runs deterministic-first or LLM comparative selection for an investigation step.</td>
                    </tr>
                    <tr>
                        <td><span class="badge bg-success">GET</span></td>
                        <td><code>/projects/{id}/capability-gaps</code></td>
                        <td>Retrieves all open and resolved capability gaps for a project.</td>
                    </tr>
                    <tr>
                        <td><span class="badge bg-info text-dark">PATCH</span></td>
                        <td><code>/capability-gaps/{id}</code></td>
                        <td>Updates gap resolution status (<code>in_development</code>, <code>resolved</code>, <code>waived</code>).</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</div>

<?php require_once __DIR__ . '/includes/help_footer.php'; ?>
