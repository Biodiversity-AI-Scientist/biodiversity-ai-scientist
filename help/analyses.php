<?php

declare(strict_types=1);

$activeTopic = 'analyses';
$pageTitle = 'Empirical Analyses & Execution — AI Scientist Help';

require_once __DIR__ . '/includes/help_header.php';

?>

<div class="row mb-4">
    <div class="col-12">
        <div class="d-flex align-items-center gap-2 mb-1">
            <span class="badge bg-danger text-white text-uppercase tracking-wide">Experiments &amp; Execution</span>
            <h1 class="h3 mb-0 fw-bold">Empirical Analyses, Experiment Plans &amp; Execution Runs</h1>
        </div>
        <p class="text-muted mb-0">
            Pre-specifying computational parameters, executing deterministic experiment runs, logging performance metrics, and persisting scientific artifacts.
        </p>
    </div>
</div>

<div class="row g-4">
    <div class="col-lg-8">
        <div class="card shadow-sm border-0 mb-4">
            <div class="card-header bg-white py-3">
                <h5 class="fw-bold text-dark mb-0"><i class="bi bi-flask text-primary me-2"></i>Analysis Execution Hierarchy</h5>
            </div>
            <div class="card-body p-4">
                <p>
                    Every computational experiment follows the canonical <strong>Experiment &amp; ExperimentRun</strong> domain model:
                </p>

                <div class="table-responsive mb-4">
                    <table class="table table-bordered table-sm align-middle spec-table">
                        <thead>
                            <tr>
                                <th>Canonical Entity</th>
                                <th>Canonical Endpoint</th>
                                <th>Description &amp; Schema Role</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td class="fw-bold"><code>Experiment</code></td>
                                <td><code>/experiments</code></td>
                                <td>Pre-specified experimental protocol containing methodology, parameter justifications, and binding to an <code>InvestigationStep</code>. <em>(Legacy: <code>AnalysisPlan</code>)</em></td>
                            </tr>
                            <tr>
                                <td class="fw-bold"><code>ExperimentRun</code></td>
                                <td><code>/experiment-runs</code></td>
                                <td>A discrete execution instance of an Experiment, tracking start/finish timestamps, exit codes, and stdout/stderr execution logs. <em>(Legacy: <code>AnalysisRun</code>)</em></td>
                            </tr>
                            <tr>
                                <td class="fw-bold"><code>Result</code></td>
                                <td><code>/experiment-runs/{id}/results</code></td>
                                <td>Structured empirical outcomes emitted by the run (e.g. classification matrices, confusion tables, silhouette scores).</td>
                            </tr>
                            <tr>
                                <td class="fw-bold"><code>Analysis</code></td>
                                <td><code>/analyses</code></td>
                                <td>Scientific synthesis, hypothesis testing, and biological interpretation of empirical experiment results.</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <h6 class="fw-bold text-dark mb-2"><i class="bi bi-folder-check text-success me-2"></i>Project Artifact Hierarchy</h6>
                <p class="small text-muted mb-2">
                    Artifacts are saved into an immutable, project-partitioned directory tree on shared storage:
                </p>
                <div class="code-snippet mb-0">
/projects/project_{id}/
├── datasets/     # Verified occurrence CSVs & cropped specimen images
├── embeddings/   # DINOv3 384-dimensional feature vector matrices (.parquet)
├── models/       # Trained model checkpoints (.pt, .pth)
└── results/      # Evaluation figures, PCA scatter plots, confusion matrices
                </div>
            </div>
        </div>
    </div>

    <div class="col-lg-4">
        <div class="card shadow-sm border-0 mb-4">
            <div class="card-header bg-white py-3">
                <h6 class="fw-bold text-dark mb-0"><i class="bi bi-play-circle me-2"></i>Execution Status Lifecycle</h6>
            </div>
            <div class="card-body p-3">
                <ul class="list-group list-group-flush small">
                    <li class="list-group-item d-flex justify-content-between align-items-center px-0">
                        <span><span class="badge bg-secondary me-2">pending</span> Queued for execution</span>
                    </li>
                    <li class="list-group-item d-flex justify-content-between align-items-center px-0">
                        <span><span class="badge bg-primary me-2">running</span> Running on GPU / worker</span>
                    </li>
                    <li class="list-group-item d-flex justify-content-between align-items-center px-0">
                        <span><span class="badge bg-success me-2">completed</span> Succeeded with metrics</span>
                    </li>
                    <li class="list-group-item d-flex justify-content-between align-items-center px-0">
                        <span><span class="badge bg-danger me-2">failed</span> Errored during run</span>
                    </li>
                </ul>
            </div>
        </div>
    </div>
</div>

<?php require_once __DIR__ . '/includes/help_footer.php'; ?>
