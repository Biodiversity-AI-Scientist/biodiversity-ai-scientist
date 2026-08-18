<?php

declare(strict_types=1);

require_once __DIR__ . '/includes/api.php';
require_once __DIR__ . '/includes/functions.php';

$project = null;
$error = null;
$flashSuccess = null;
$brainstormingSessions = [];
$researchPlans = [];
$questionsCount = 0;
$hypothesesCount = 0;
$investigationStepsCount = 0;
$experimentsCount = 0;
$hasApprovedPlan = false;
$approvedPlan = null;

try {
    $projectId = getRequiredPositiveInt('project_id');

    // Handle POST actions for updating project details
    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        $action = trim($_POST['action'] ?? '');
        if ($action === 'update_project_details') {
            $newTitle = trim($_POST['title'] ?? '');
            $newObjective = trim($_POST['objective'] ?? '');
            $newStatus = trim($_POST['status'] ?? '');
            if ($newTitle === '') {
                throw new InvalidArgumentException('Project title cannot be empty.');
            }
            api_patch('/projects/' . $projectId, [
                'title' => $newTitle,
                'objective' => $newObjective !== '' ? $newObjective : null,
                'status' => $newStatus !== '' ? $newStatus : null,
            ]);
            header('Location: project.php?project_id=' . $projectId . '&updated=1');
            exit;
        }
    }

    if (isset($_GET['updated'])) {
        $flashSuccess = 'Project title and description updated successfully.';
    }

    $project = api_get('/projects/' . $projectId);

    // Fetch brainstorming sessions
    try {
        $brainstormingSessions = api_get('/projects/' . $projectId . '/brainstorming-sessions');
    } catch (Throwable $e) {
        $brainstormingSessions = [];
    }

    // Fetch research plans
    try {
        $researchPlans = api_get('/projects/' . $projectId . '/research-plans');
        if (is_array($researchPlans)) {
            foreach ($researchPlans as $rp) {
                if (($rp['status'] ?? '') === 'approved') {
                    $hasApprovedPlan = true;
                    $approvedPlan = $rp;
                    break;
                }
            }
        }
    } catch (Throwable $e) {
        $researchPlans = [];
    }

    // Fetch questions
    try {
        $questions = api_get('/projects/' . $projectId . '/questions');
        $questionsCount = is_array($questions) ? count($questions) : 0;
    } catch (Throwable $e) {
        $questionsCount = 0;
    }

    // Fetch hypotheses
    try {
        $hypotheses = api_get('/projects/' . $projectId . '/hypotheses');
        $hypothesesCount = is_array($hypotheses) ? count($hypotheses) : 0;
    } catch (Throwable $e) {
        $hypothesesCount = 0;
    }

    // Fetch investigation steps (Phase 8 DAG)
    try {
        $investigationSteps = api_get('/projects/' . $projectId . '/investigation-steps');
        $investigationStepsCount = is_array($investigationSteps) ? count($investigationSteps) : 0;
    } catch (Throwable $e) {
        $investigationStepsCount = 0;
    }

    // Fetch experiments (Analysis Plans)
    try {
        $experiments = api_get('/projects/' . $projectId . '/analysis-plans');
        $experimentsCount = is_array($experiments) ? count($experiments) : 0;
    } catch (Throwable $e) {
        $experimentsCount = 0;
    }

} catch (Throwable $e) {
    $projectId = 0;
    $error = $e->getMessage();
}

$activePage = 'overview';

?>
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>
        <?php if ($project !== null): ?>
            <?= h($project['title']) ?> &mdash;
        <?php endif; ?>
        Biodiversity AI Scientist
    </title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="/ai-scientist/css/app.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
    <style>
        .workflow-step-card {
            transition: all 0.2s ease-in-out;
            text-decoration: none !important;
            display: block;
        }
        .workflow-step-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 .25rem .75rem rgba(0,0,0,.08);
        }
    </style>
</head>
<body class="bg-light">

<?php require_once __DIR__ . '/includes/navbar.php'; ?>

<?php if ($error !== null && $project === null): ?>
    <div class="container py-5">
        <div class="alert alert-danger">
            <h1 class="h5"><i class="bi bi-exclamation-triangle-fill me-2"></i>Unable to open project</h1>
            <p class="mb-3"><?= h($error) ?></p>
            <a href="/ai-scientist/projects.php" class="btn btn-outline-danger">Back to projects</a>
        </div>
    </div>
<?php else: ?>

<div class="container-fluid">
    <!-- Project heading & Objective Banner -->
    <div class="row border-bottom bg-white shadow-sm">
        <div class="col-12 px-4 py-3">
            <div class="d-flex justify-content-between align-items-start">
                <div class="flex-grow-1 me-3">
                    <div class="d-flex align-items-center gap-2 mb-1">
                        <span class="text-muted small">
                            <i class="bi bi-folder2 me-1"></i>Research Project #<?= (int)$project['id'] ?>
                        </span>
                        <span class="badge <?= statusBadge($project['status']) ?>">
                            <?= h(ucfirst($project['status'])) ?>
                        </span>
                        <?php if (!empty($project['archived_at'])): ?>
                            <span class="badge bg-secondary">Archived</span>
                        <?php endif; ?>
                    </div>
                    <h1 class="h3 mb-2 text-dark fw-bold">
                        <?= h($project['title']) ?>
                    </h1>
                    <?php if (!empty($project['objective'])): ?>
                        <div class="p-3 bg-light border rounded text-secondary fs-6 mt-2">
                            <div class="fw-semibold text-dark small text-uppercase mb-1">
                                <i class="bi bi-card-text text-primary me-1"></i>Project Objective / Description
                            </div>
                            <?= nl2br(h($project['objective'])) ?>
                        </div>
                    <?php else: ?>
                        <div class="text-muted small fst-italic mt-1">
                            <i class="bi bi-info-circle me-1"></i>No description / research objective provided yet. Click <strong>Edit Details</strong> to add one.
                        </div>
                    <?php endif; ?>
                </div>
                <div class="d-flex gap-2 flex-shrink-0 flex-wrap">
                    <a href="/projects/<?= (int)$project['id'] ?>/export" target="_blank" download="bais_project_<?= (int)$project['id'] ?>_export.json" class="btn btn-outline-success btn-sm" title="Download complete research archive as JSON">
                        <i class="bi bi-download me-1"></i>Export Project (JSON)
                    </a>
                    <button type="button" class="btn btn-outline-primary btn-sm" data-bs-toggle="modal" data-bs-target="#editProjectModal">
                        <i class="bi bi-pencil me-1"></i>Edit Details
                    </button>
                    <a href="/ai-scientist/projects.php" class="btn btn-outline-secondary btn-sm">
                        <i class="bi bi-arrow-left me-1"></i>All projects
                    </a>
                </div>
            </div>
        </div>
    </div>

    <div class="row">
        <!-- Shared workspace menu -->
        <?php require __DIR__ . '/includes/menu.php'; ?>

        <!-- Main workspace -->
        <main class="col-md-9 col-lg-10 p-4">

            <?php if ($flashSuccess !== null): ?>
                <div class="alert alert-success alert-dismissible fade show" role="alert">
                    <i class="bi bi-check-circle me-1"></i> <?= htmlspecialchars($flashSuccess, ENT_QUOTES, 'UTF-8') ?>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            <?php endif; ?>

            <?php if ($error !== null): ?>
                <div class="alert alert-danger alert-dismissible fade show" role="alert">
                    <i class="bi bi-exclamation-triangle me-1"></i> <?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            <?php endif; ?>

            <!-- Scientific Lifecycle Pipeline Banner (Dynamic & Interactive) -->
            <div class="card shadow-sm border-0 mb-4 bg-white">
                <div class="card-header bg-dark text-white d-flex justify-content-between align-items-center py-2 px-3">
                    <span class="fw-bold font-monospace small">
                        <i class="bi bi-diagram-3-fill text-primary me-2"></i>Scientific Workflow Lifecycle
                    </span>
                    <a href="help/user_manual.php?project_id=<?= $projectId ?>" class="text-light text-decoration-none small">
                        📖 View Guide &amp; Spec &rarr;
                    </a>
                </div>
                <div class="card-body p-3">
                    <div class="row g-2 text-center small font-monospace">
                        
                        <!-- Step 1: Ideate -->
                        <?php $s1Active = count($brainstormingSessions) > 0; ?>
                        <div class="col">
                            <a href="brainstorming.php?project_id=<?= $projectId ?>" class="workflow-step-card p-2 border rounded h-100 <?= $s1Active ? 'bg-primary bg-opacity-10 border-primary' : 'bg-light text-muted border-secondary-subtle' ?>">
                                <span class="badge <?= $s1Active ? 'bg-primary' : 'bg-secondary' ?> mb-1">Step 1: Ideate</span>
                                <div class="fw-bold <?= $s1Active ? 'text-primary' : 'text-dark' ?>">Brainstorming</div>
                                <div class="text-muted small mt-1" style="font-size: 11px;">
                                    <?= $s1Active ? count($brainstormingSessions) . ' Session' . (count($brainstormingSessions) === 1 ? '' : 's') : 'Start AI dialogue' ?>
                                </div>
                            </a>
                        </div>

                        <!-- Step 2: Plan -->
                        <?php 
                            $s2Active = count($researchPlans) > 0;
                            $s2Approved = $hasApprovedPlan;
                        ?>
                        <div class="col">
                            <a href="research_plans.php?project_id=<?= $projectId ?>" class="workflow-step-card p-2 border rounded h-100 <?= $s2Approved ? 'bg-success bg-opacity-10 border-success' : ($s2Active ? 'bg-warning bg-opacity-10 border-warning' : 'bg-light text-muted border-secondary-subtle') ?>">
                                <span class="badge <?= $s2Approved ? 'bg-success' : ($s2Active ? 'bg-warning text-dark' : 'bg-secondary') ?> mb-1">Step 2: Plan</span>
                                <div class="fw-bold <?= $s2Approved ? 'text-success' : ($s2Active ? 'text-warning-emphasis' : 'text-dark') ?>">Research Plan</div>
                                <div class="text-muted small mt-1" style="font-size: 11px;">
                                    <?= $s2Approved ? 'v' . (int)$approvedPlan['version'] . ' Approved' : ($s2Active ? count($researchPlans) . ' Draft Plan' . (count($researchPlans) === 1 ? '' : 's') : 'Synthesize plan') ?>
                                </div>
                            </a>
                        </div>

                        <!-- Step 3: Investigation Plan (Phase 8 DAG) -->
                        <?php $s3Active = $investigationStepsCount > 0; ?>
                        <div class="col">
                            <a href="investigation_plan.php?project_id=<?= $projectId ?>" class="workflow-step-card p-2 border rounded h-100 <?= $s3Active ? 'bg-info bg-opacity-10 border-info' : 'bg-light text-muted border-secondary-subtle' ?>">
                                <span class="badge <?= $s3Active ? 'bg-info text-dark' : 'bg-secondary' ?> mb-1">Step 3: Sequencing</span>
                                <div class="fw-bold <?= $s3Active ? 'text-info-emphasis' : 'text-dark' ?>">Investigation Plan</div>
                                <div class="text-muted small mt-1" style="font-size: 11px;">
                                    <?= $s3Active ? $investigationStepsCount . ' Steps (DAG)' : ($s2Approved ? 'Ready to sequence' : 'Needs approved plan') ?>
                                </div>
                            </a>
                        </div>

                        <!-- Step 4: Canonicalize -->
                        <?php $s4Active = ($questionsCount > 0 || $hypothesesCount > 0); ?>
                        <div class="col">
                            <a href="questions.php?project_id=<?= $projectId ?>" class="workflow-step-card p-2 border rounded h-100 <?= $s4Active ? 'bg-primary-subtle border-primary-subtle' : 'bg-light text-muted border-secondary-subtle' ?>">
                                <span class="badge <?= $s4Active ? 'bg-primary' : 'bg-secondary' ?> mb-1">Step 4: Formulate</span>
                                <div class="fw-bold <?= $s4Active ? 'text-primary' : 'text-dark' ?>">Questions &amp; Hypotheses</div>
                                <div class="text-muted small mt-1" style="font-size: 11px;">
                                    <?= $s4Active ? $questionsCount . ' Q / ' . $hypothesesCount . ' H' : 'Audit records' ?>
                                </div>
                            </a>
                        </div>

                        <!-- Step 5: Execute -->
                        <?php $s5Active = $experimentsCount > 0; ?>
                        <div class="col">
                            <a href="analyses.php?project_id=<?= $projectId ?>" class="workflow-step-card p-2 border rounded h-100 <?= $s5Active ? 'bg-success bg-opacity-10 border-success' : 'bg-light text-muted border-secondary-subtle' ?>">
                                <span class="badge <?= $s5Active ? 'bg-success' : 'bg-secondary' ?> mb-1">Step 5: Execute</span>
                                <div class="fw-bold <?= $s5Active ? 'text-success' : 'text-dark' ?>">Datasets &amp; Experiments</div>
                                <div class="text-muted small mt-1" style="font-size: 11px;">
                                    <?= $s5Active ? $experimentsCount . ' Experiment' . ($experimentsCount === 1 ? '' : 's') : 'Runs &amp; Results' ?>
                                </div>
                            </a>
                        </div>

                    </div>
                </div>
            </div>

            <div class="row g-4">

                <!-- Phase 1 Card: Brainstorming Workspace -->
                <div class="col-md-6 col-xl-4">
                    <div class="card shadow-sm workspace-card h-100 border-primary">
                        <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
                            <span class="fw-bold"><i class="bi bi-lightbulb me-1"></i> Brainstorming</span>
                            <span class="badge bg-light text-primary"><?= count($brainstormingSessions) ?> Sessions</span>
                        </div>
                        <div class="card-body d-flex flex-column justify-content-between">
                            <div>
                                <p class="text-muted small mb-3">
                                    Collaborative AI ideation environment. Discuss morphological variations, confounders, and sampling hypotheses.
                                </p>
                                <?php if (!empty($brainstormingSessions)): ?>
                                    <?php $latestSession = $brainstormingSessions[0]; ?>
                                    <div class="bg-light p-2 border rounded small mb-3">
                                        <div class="d-flex justify-content-between">
                                            <strong>Latest Session #<?= (int)$latestSession['id'] ?>:</strong>
                                            <span class="badge bg-success"><?= h($latestSession['status']) ?></span>
                                        </div>
                                        <div class="text-truncate text-muted mt-1">
                                            <?= h($latestSession['initial_idea']) ?>
                                        </div>
                                    </div>
                                <?php endif; ?>
                            </div>
                            <div>
                                <a href="brainstorming.php?project_id=<?= $projectId ?>" class="btn btn-sm btn-primary w-100">
                                    <?= empty($brainstormingSessions) ? '+ Start Brainstorming' : 'Open Brainstorming Workspace' ?>
                                </a>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Phase 2 Card: Structured Research Plans -->
                <div class="col-md-6 col-xl-4">
                    <div class="card shadow-sm workspace-card h-100 border-success">
                        <div class="card-header bg-success text-white d-flex justify-content-between align-items-center">
                            <span class="fw-bold"><i class="bi bi-journal-text me-1"></i> Research Plans</span>
                            <span class="badge bg-light text-success"><?= count($researchPlans) ?> Plans</span>
                        </div>
                        <div class="card-body d-flex flex-column justify-content-between">
                            <div>
                                <p class="text-muted small mb-3">
                                    Rigorous 20-field scientific study plans synthesized from brainstorming. Supports version lineage (v1 &rarr; v2), review, and approval.
                                </p>
                                <?php if (!empty($researchPlans)): ?>
                                    <?php $latestPlan = $researchPlans[0]; ?>
                                    <div class="bg-light p-2 border rounded small mb-3">
                                        <div class="d-flex justify-content-between">
                                            <strong>Version <?= (int)$latestPlan['version'] ?>: <?= h(mb_strimwidth($latestPlan['title'], 0, 26, '...')) ?></strong>
                                            <span class="badge <?= $latestPlan['status'] === 'approved' ? 'bg-success' : 'bg-warning text-dark' ?>">
                                                <?= h($latestPlan['status']) ?>
                                            </span>
                                        </div>
                                    </div>
                                <?php endif; ?>
                            </div>
                            <div>
                                <a href="research_plans.php?project_id=<?= $projectId ?>" class="btn btn-sm btn-success w-100">
                                    <?= empty($researchPlans) ? 'View Research Plans' : 'View Research Plans (' . count($researchPlans) . ')' ?>
                                </a>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Phase 8 Card: Investigation Plan & Step Sequencing -->
                <div class="col-md-6 col-xl-4">
                    <div class="card shadow-sm workspace-card h-100 border-info">
                        <div class="card-header bg-info text-dark d-flex justify-content-between align-items-center">
                            <span class="fw-bold"><i class="bi bi-diagram-3 me-1"></i> Investigation Plan (DAG)</span>
                            <span class="badge bg-dark text-white"><?= $investigationStepsCount ?> Steps</span>
                        </div>
                        <div class="card-body d-flex flex-column justify-content-between">
                            <div>
                                <p class="text-muted small mb-3">
                                    Explicit Directed Acyclic Graph (DAG) of investigation steps with computed prerequisite readiness, capabilities, and experiment links.
                                </p>
                                <div class="bg-light p-2 border rounded small mb-3">
                                    <div class="d-flex justify-content-between align-items-center">
                                        <span>Status:</span>
                                        <span class="badge <?= $investigationStepsCount > 0 ? 'bg-info text-dark' : ($hasApprovedPlan ? 'bg-primary' : 'bg-secondary') ?>">
                                            <?= $investigationStepsCount > 0 ? 'DAG Configured' : ($hasApprovedPlan ? 'Ready to Generate' : 'Requires Approved Plan') ?>
                                        </span>
                                    </div>
                                </div>
                            </div>
                            <div>
                                <a href="investigation_plan.php?project_id=<?= $projectId ?>" class="btn btn-sm btn-outline-info text-dark w-100">
                                    <?= $investigationStepsCount > 0 ? 'Open Investigation DAG' : 'Build Investigation DAG' ?>
                                </a>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Research Questions -->
                <div class="col-md-6 col-xl-4">
                    <div class="card shadow-sm workspace-card h-100">
                        <div class="card-body d-flex flex-column justify-content-between">
                            <div>
                                <h2 class="h5"><i class="bi bi-question-circle text-primary me-2"></i>Research Questions</h2>
                                <p class="text-muted small mb-3">
                                    Canonical scientific questions and subquestions defining the focal investigation.
                                </p>
                            </div>
                            <a href="questions.php?project_id=<?= $projectId ?>" class="btn btn-sm btn-outline-primary w-100">
                                View questions (<?= $questionsCount ?>)
                            </a>
                        </div>
                    </div>
                </div>

                <!-- Hypotheses -->
                <div class="col-md-6 col-xl-4">
                    <div class="card shadow-sm workspace-card h-100">
                        <div class="card-body d-flex flex-column justify-content-between">
                            <div>
                                <h2 class="h5"><i class="bi bi-hypnotize text-primary me-2"></i>Hypotheses</h2>
                                <p class="text-muted small mb-3">
                                    Explicit testable hypotheses, mechanisms, and predictions linked to questions.
                                </p>
                            </div>
                            <a href="hypotheses.php?project_id=<?= $projectId ?>" class="btn btn-sm btn-outline-primary w-100">
                                View hypotheses (<?= $hypothesesCount ?>)
                            </a>
                        </div>
                    </div>
                </div>

                <!-- Dataset & Experiments -->
                <div class="col-md-6 col-xl-4">
                    <div class="card shadow-sm workspace-card h-100">
                        <div class="card-body d-flex flex-column justify-content-between">
                            <div>
                                <h2 class="h5"><i class="bi bi-flask text-success me-2"></i>Experiments &amp; Datasets</h2>
                                <p class="text-muted small mb-3">
                                    Pre-specified computational / empirical experiments and recorded runs.
                                </p>
                            </div>
                            <div class="d-flex gap-2">
                                <a href="analyses.php?project_id=<?= $projectId ?>" class="btn btn-sm btn-outline-success flex-fill">
                                    Experiments (<?= $experimentsCount ?>)
                                </a>
                                <a href="dataset.php?project_id=<?= $projectId ?>" class="btn btn-sm btn-outline-secondary flex-fill">
                                    Datasets
                                </a>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Project state table -->
                <div class="col-lg-6">
                    <div class="card shadow-sm border-0">
                        <div class="card-header bg-white fw-bold">
                            <i class="bi bi-info-circle me-1"></i> Project State
                        </div>
                        <div class="card-body p-0">
                            <table class="table mb-0 small">
                                <tbody>
                                <tr>
                                    <th style="width: 35%;">Project ID</th>
                                    <td>#<?= (int)$project['id'] ?></td>
                                </tr>
                                <tr>
                                    <th>Lifecycle Status</th>
                                    <td><span class="badge <?= statusBadge($project['status']) ?>"><?= h(ucfirst($project['status'])) ?></span></td>
                                </tr>
                                <tr>
                                    <th>Approved Strategy</th>
                                    <td>
                                        <?php if ($hasApprovedPlan): ?>
                                            <span class="badge bg-success">v<?= (int)$approvedPlan['version'] ?> Approved</span>
                                        <?php else: ?>
                                            <span class="badge bg-secondary">No approved plan</span>
                                        <?php endif; ?>
                                    </td>
                                </tr>
                                <tr>
                                    <th>Investigation Steps</th>
                                    <td><?= $investigationStepsCount ?> step<?= $investigationStepsCount === 1 ? '' : 's' ?> in DAG</td>
                                </tr>
                                <tr>
                                    <th>Created</th>
                                    <td>
                                        <?php
                                        $created = new DateTime($project['created_at']);
                                        echo h($created->format('Y-m-d H:i:s'));
                                        ?>
                                    </td>
                                </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- Next proposed action -->
                <div class="col-lg-6">
                    <div class="card shadow-sm border-0">
                        <div class="card-header bg-white fw-bold">
                            <i class="bi bi-compass me-1"></i> Next Proposed Scientific Action
                        </div>
                        <div class="card-body">
                            <?php if (empty($brainstormingSessions)): ?>
                                <p class="text-muted mb-2">No brainstorming session started yet.</p>
                                <a href="brainstorming.php?project_id=<?= $projectId ?>" class="btn btn-sm btn-primary">
                                    <i class="bi bi-lightbulb me-1"></i>Start initial brainstorming session &rarr;
                                </a>
                            <?php elseif (!$hasApprovedPlan): ?>
                                <p class="text-muted mb-2">Brainstorming session active. Ready to synthesize or approve research plan.</p>
                                <a href="research_plans.php?project_id=<?= $projectId ?>" class="btn btn-sm btn-success">
                                    <i class="bi bi-journal-check me-1"></i>Synthesize / Approve Research Plan &rarr;
                                </a>
                            <?php elseif ($investigationStepsCount === 0): ?>
                                <p class="text-muted mb-2">Approved Research Plan in place. Ready to sequence the investigation DAG.</p>
                                <a href="investigation_plan.php?project_id=<?= $projectId ?>" class="btn btn-sm btn-info text-dark">
                                    <i class="bi bi-diagram-3 me-1"></i>Generate Investigation Plan DAG &rarr;
                                </a>
                            <?php else: ?>
                                <p class="text-muted mb-2">Investigation DAG active with <?= $investigationStepsCount ?> steps. Ready for capability execution &amp; experiment runs.</p>
                                <a href="investigation_plan.php?project_id=<?= $projectId ?>" class="btn btn-sm btn-outline-primary">
                                    <i class="bi bi-play-circle me-1"></i>View Investigation DAG &amp; Prerequisites &rarr;
                                </a>
                            <?php endif; ?>
                        </div>
                    </div>
                </div>

            </div>

        </main>
    </div>
</div>

<!-- Edit Project Details Modal -->
<div class="modal fade" id="editProjectModal" tabindex="-1" aria-labelledby="editProjectModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
            <form method="post" action="project.php?project_id=<?= (int)$project['id'] ?>">
                <input type="hidden" name="action" value="update_project_details">
                <div class="modal-header bg-dark text-white">
                    <h5 class="modal-title" id="editProjectModalLabel">
                        <i class="bi bi-pencil-square text-primary me-2"></i>Edit Project Details
                    </h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div class="mb-3">
                        <label for="editTitle" class="form-label fw-semibold">Project Title <span class="text-danger">*</span></label>
                        <input type="text" class="form-control" id="editTitle" name="title" required value="<?= htmlspecialchars($project['title'], ENT_QUOTES, 'UTF-8') ?>">
                    </div>
                    <div class="mb-3">
                        <label for="editObjective" class="form-label fw-semibold">Project Objective / Description</label>
                        <textarea class="form-control" id="editObjective" name="objective" rows="5"><?= htmlspecialchars($project['objective'] ?? '', ENT_QUOTES, 'UTF-8') ?></textarea>
                        <div class="form-text">Describe the primary scientific objective, focal taxa, and biological hypotheses.</div>
                    </div>
                    <div class="mb-3">
                        <label for="editStatus" class="form-label fw-semibold">Status</label>
                        <select class="form-select" id="editStatus" name="status">
                            <option value="draft" <?= $project['status'] === 'draft' ? 'selected' : '' ?>>Draft</option>
                            <option value="active" <?= $project['status'] === 'active' ? 'selected' : '' ?>>Active</option>
                            <option value="completed" <?= $project['status'] === 'completed' ? 'selected' : '' ?>>Completed</option>
                            <option value="archived" <?= $project['status'] === 'archived' ? 'selected' : '' ?>>Archived</option>
                        </select>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn btn-primary">
                        <i class="bi bi-check-lg me-1"></i>Save Changes
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>

<?php endif; ?>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
