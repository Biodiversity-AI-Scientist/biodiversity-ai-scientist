<?php

declare(strict_types=1);

require_once __DIR__ . '/includes/api.php';
require_once __DIR__ . '/includes/functions.php';

$projectId = 0;
$project = null;
$plans = [];
$selectedPlan = null;
$selectedPlanId = 0;
$error = null;
$flashSuccess = null;
$showArchived = !empty($_GET['show_archived']);
$showArch = $showArchived ? '&show_archived=1' : '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    try {
        $projectId = getRequiredPositiveInt('project_id');
        $action = trim($_POST['action'] ?? '');
        $planId = (int)($_POST['plan_id'] ?? 0);

        if ($action === 'approve_plan' && $planId > 0) {
            api_post('/research-plans/' . $planId . '/approve', []);
            header('Location: research_plans.php?project_id=' . $projectId . '&plan_id=' . $planId . '&approved=1' . $showArch);
            exit;
        }

        if ($action === 'revise_plan' && $planId > 0) {
            $steering = trim($_POST['steering_instructions'] ?? '');
            if ($steering === '') {
                throw new InvalidArgumentException('Steering instructions cannot be empty.');
            }
            $revised = api_post('/research-plans/' . $planId . '/revise', [
                'steering_instructions' => $steering
            ]);
            header('Location: research_plans.php?project_id=' . $projectId . '&plan_id=' . $revised['id'] . '&revised=1' . $showArch);
            exit;
        }

        if ($action === 'promote_plan' && $planId > 0) {
            $qIndices = isset($_POST['questions']) && is_array($_POST['questions']) ? array_map('intval', $_POST['questions']) : [];
            $hIndices = isset($_POST['hypotheses']) && is_array($_POST['hypotheses']) ? array_map('intval', $_POST['hypotheses']) : [];

            $result = api_post('/research-plans/' . $planId . '/promote', [
                'question_indices' => $qIndices,
                'hypothesis_indices' => $hIndices
            ]);

            $msg = 'Promoted ' . count($result['promoted_question_ids'] ?? []) . ' research questions and ' . count($result['promoted_hypothesis_ids'] ?? []) . ' hypotheses to canonical project tables.';
            header('Location: research_plans.php?project_id=' . $projectId . '&plan_id=' . $planId . '&promoted_msg=' . urlencode($msg) . $showArch);
            exit;
        }

        if ($action === 'archive_plan' && $planId > 0) {
            api_patch('/research-plans/' . $planId . '/archive');
            header('Location: research_plans.php?project_id=' . $projectId . '&archived=1' . $showArch);
            exit;
        }

        if ($action === 'unarchive_plan' && $planId > 0) {
            api_patch('/research-plans/' . $planId . '/unarchive');
            header('Location: research_plans.php?project_id=' . $projectId . '&plan_id=' . $planId . '&unarchived=1' . $showArch);
            exit;
        }
    } catch (Throwable $e) {
        $error = $e->getMessage();
    }
}

try {
    if ($projectId === 0) {
        $projectId = getRequiredPositiveInt('project_id');
    }

    $project = api_get('/projects/' . $projectId);
    $plans = api_get('/projects/' . $projectId . '/research-plans?include_archived=' . ($showArchived ? 'true' : 'false'));

    $requestedPlanId = isset($_GET['plan_id']) ? (int)$_GET['plan_id'] : 0;
    if ($requestedPlanId > 0) {
        $selectedPlanId = $requestedPlanId;
    } elseif (!empty($plans)) {
        $selectedPlanId = (int)$plans[0]['id'];
    }

    if ($selectedPlanId > 0) {
        $selectedPlan = api_get('/research-plans/' . $selectedPlanId);
    }
} catch (Throwable $e) {
    if ($error === null) {
        $error = $e->getMessage();
    }
}

if (isset($_GET['approved'])) {
    $flashSuccess = 'Research Plan approved successfully! Status updated to approved.';
} elseif (isset($_GET['revised'])) {
    $flashSuccess = 'Research Plan revised with AI steering instructions. New plan version generated!';
} elseif (isset($_GET['promoted_msg'])) {
    $flashSuccess = urldecode($_GET['promoted_msg']);
} elseif (isset($_GET['archived'])) {
    $flashSuccess = 'Research plan archived/hidden from active list.';
} elseif (isset($_GET['unarchived'])) {
    $flashSuccess = 'Research plan unarchived and restored to active list.';
}

$activePage = 'research_plans';

?>
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Research Plans - Biodiversity AI Scientist</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="css/app.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
</head>
<body class="bg-light">

<?php require_once __DIR__ . '/includes/navbar.php'; ?>


<?php if ($error !== null && $project === null): ?>
    <div class="container py-5">
        <div class="alert alert-danger">
            <h1 class="h5">Unable to load project research plans</h1>
            <p class="mb-3"><?= h($error) ?></p>
            <a href="projects.php" class="btn btn-outline-danger">Back to projects</a>
        </div>
    </div>
<?php else: ?>

    <div class="container-fluid">
        <div class="row border-bottom bg-white">
            <div class="col-12 px-4 py-3">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <div class="text-muted small mb-1">Research Project #<?= (int)$project['id'] ?></div>
                        <h1 class="h4 mb-1"><?= h($project['title']) ?></h1>
                        <?php if (!empty($project['objective'])): ?>
                            <div class="text-muted small mt-1">
                                <i class="bi bi-card-text text-primary me-1"></i><?= h($project['objective']) ?>
                            </div>
                        <?php endif; ?>
                    </div>
                    <div class="d-flex gap-2 align-items-center">
                        <a href="help/research_plans.php?project_id=<?= $projectId ?>" class="btn btn-sm btn-outline-info text-dark">
                            📖 User Guide &amp; Spec
                        </a>
                        <a href="project.php?project_id=<?= $projectId ?>" class="btn btn-sm btn-outline-secondary">Project overview</a>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <?php require __DIR__ . '/includes/menu.php'; ?>

            <main class="col-md-9 col-lg-10 p-4">

                <?php if ($error !== null): ?>
                    <div class="alert alert-danger alert-dismissible fade show" role="alert">
                        <strong>Error:</strong> <?= h($error) ?>
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                <?php endif; ?>

                <?php if ($flashSuccess !== null): ?>
                    <div class="alert alert-success alert-dismissible fade show" role="alert">
                        <?= h($flashSuccess) ?>
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                <?php endif; ?>

                <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
                    <div>
                        <h2 class="h3 mb-1">Structured Research Plans</h2>
                        <p class="text-muted mb-0">Versioned 20-field scientific study plans drafted and revised during brainstorming.</p>
                    </div>
                    <div class="d-flex gap-2 align-items-center">
                        <a href="help/research_plans.php?project_id=<?= $projectId ?>" class="btn btn-outline-primary btn-sm">
                            <i class="bi bi-question-circle me-1"></i>Guide: Purpose &amp; Workflow
                        </a>
                        <a href="brainstorming.php?project_id=<?= $projectId ?>" class="btn btn-primary btn-sm">
                            + Generate Plan from Brainstorming
                        </a>
                    </div>
                </div>


                <?php if (empty($plans)): ?>
                    <div class="card shadow-sm">
                        <div class="card-body text-center py-5">
                            <h3 class="h5 mb-2">No Research Plans Created Yet</h3>
                            <p class="text-muted mb-4">Start a brainstorming session to explore research ideas and generate a structured 20-field scientific Research Plan.</p>
                            <a href="brainstorming.php?project_id=<?= $projectId ?>" class="btn btn-primary btn-lg">
                                Start Brainstorming
                            </a>
                        </div>
                    </div>
                <?php else: ?>

                    <div class="row g-4">
                        <!-- Plans List (Left Column) -->
                        <div class="col-lg-4">
                            <div class="card shadow-sm">
                                <div class="card-header bg-white fw-bold d-flex justify-content-between align-items-center">
                                    <span>Saved Plans (<?= count($plans) ?>)</span>
                                    <a href="research_plans.php?project_id=<?= $projectId ?>&show_archived=<?= $showArchived ? '0' : '1' ?><?= $selectedPlanId > 0 ? '&plan_id=' . $selectedPlanId : '' ?>"
                                       class="btn btn-sm btn-link p-0 text-decoration-none small text-secondary">
                                        <?= $showArchived ? 'Hide Archived' : 'Show Archived' ?>
                                    </a>
                                </div>
                                <div class="list-group list-group-flush">
                                    <?php foreach ($plans as $p): ?>
                                        <?php
                                            $isCurrent = ((int)$p['id'] === $selectedPlanId);
                                            $statusClass = 'bg-warning text-dark';
                                            if ($p['status'] === 'approved') $statusClass = 'bg-success';
                                            if ($p['status'] === 'under_review') $statusClass = 'bg-info text-dark';
                                        ?>
                                        <a href="research_plans.php?project_id=<?= $projectId ?>&plan_id=<?= (int)$p['id'] ?>"
                                           class="list-group-item list-group-item-action <?= $isCurrent ? 'active' : '' ?>">
                                            <div class="d-flex justify-content-between align-items-center mb-1">
                                                <span class="fw-bold">v<?= (int)$p['version'] ?>: <?= h(mb_strimwidth($p['title'], 0, 28, '...')) ?></span>
                                                <span class="badge <?= $statusClass ?>"><?= h($p['status']) ?></span>
                                            </div>
                                            <div class="small <?= $isCurrent ? 'text-white-50' : 'text-muted' ?>">
                                                Session #<?= (int)($p['brainstorming_session_id'] ?? 0) ?> · <?= date('M j, Y H:i', strtotime($p['created_at'])) ?>
                                            </div>
                                        </a>
                                    <?php endforeach; ?>
                                </div>
                            </div>
                        </div>

                        <!-- Plan Details View (Right Column) -->
                        <div class="col-lg-8">
                            <?php if ($selectedPlan !== null): ?>
                                <?php
                                    $c = $selectedPlan['content'] ?? [];
                                    $statusClass = 'bg-warning text-dark';
                                    if ($selectedPlan['status'] === 'approved') $statusClass = 'bg-success';
                                    if ($selectedPlan['status'] === 'under_review') $statusClass = 'bg-info text-dark';
                                ?>
                                <div class="card shadow-sm">
                                    <div class="card-header bg-white py-3">
                                        <div class="d-flex justify-content-between align-items-start">
                                            <div>
                                                <span class="badge bg-secondary me-1">Plan Version <?= (int)$selectedPlan['version'] ?></span>
                                                <span class="badge <?= $statusClass ?>"><?= h($selectedPlan['status']) ?></span>
                                                <h3 class="h4 mt-2 mb-1"><?= h($selectedPlan['title']) ?></h3>
                                                <div class="small text-muted">Originating Brainstorming Session #<?= (int)($selectedPlan['brainstorming_session_id'] ?? 0) ?></div>
                                            </div>
                                            <div class="d-flex gap-2 align-items-center">
                                                <!-- Top Header Promote / Instantiate Button -->
                                                <button type="button" class="btn btn-sm btn-primary fw-semibold shadow-sm" data-bs-toggle="modal" data-bs-target="#promoteItemsModal">
                                                    ⭐ Promote to Questions &amp; Hypotheses &rarr;
                                                </button>
                                                <!-- AI Revision Modal Trigger -->
                                                <button type="button" class="btn btn-sm btn-outline-primary" data-bs-toggle="modal" data-bs-target="#revisePlanModal">
                                                    🔄 Revise with AI
                                                </button>
                                                <!-- Approve Plan -->
                                                <?php if ($selectedPlan['status'] !== 'approved' && $selectedPlan['status'] !== 'archived'): ?>
                                                    <form method="post" action="research_plans.php?project_id=<?= $projectId ?><?= $showArch ?>">
                                                        <input type="hidden" name="action" value="approve_plan">
                                                        <input type="hidden" name="project_id" value="<?= $projectId ?>">
                                                        <input type="hidden" name="plan_id" value="<?= (int)$selectedPlan['id'] ?>">
                                                        <button type="submit" class="btn btn-sm btn-success">✔ Approve Plan</button>
                                                    </form>
                                                <?php elseif ($selectedPlan['status'] === 'approved'): ?>
                                                    <span class="btn btn-sm btn-success disabled">Approved</span>
                                                <?php endif; ?>

                                                <!-- Plan Actions Dropdown (Archive / Unarchive) -->
                                                <div class="dropdown">
                                                    <button class="btn btn-sm btn-outline-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown">
                                                        Manage
                                                    </button>
                                                    <ul class="dropdown-menu dropdown-menu-end">
                                                        <?php if ($selectedPlan['status'] === 'archived'): ?>
                                                            <li>
                                                                <form method="post" action="research_plans.php?project_id=<?= $projectId ?><?= $showArch ?>">
                                                                    <input type="hidden" name="action" value="unarchive_plan">
                                                                    <input type="hidden" name="project_id" value="<?= $projectId ?>">
                                                                    <input type="hidden" name="plan_id" value="<?= (int)$selectedPlan['id'] ?>">
                                                                    <button type="submit" class="dropdown-item text-success">Unarchive Plan</button>
                                                                </form>
                                                            </li>
                                                        <?php else: ?>
                                                            <li>
                                                                <form method="post" action="research_plans.php?project_id=<?= $projectId ?><?= $showArch ?>">
                                                                    <input type="hidden" name="action" value="archive_plan">
                                                                    <input type="hidden" name="project_id" value="<?= $projectId ?>">
                                                                    <input type="hidden" name="plan_id" value="<?= (int)$selectedPlan['id'] ?>">
                                                                    <button type="submit" class="dropdown-item text-danger" onclick="return confirm('Archive/hide this research plan from the active list?');">Archive / Hide Plan</button>
                                                                </form>
                                                            </li>
                                                        <?php endif; ?>
                                                    </ul>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="card-body p-4">
                                        <!-- Structured 20-Field Content Breakdown -->
                                        <div class="mb-4">
                                            <h5 class="h6 text-uppercase text-muted fw-bold">1. Objective & Rationale</h5>
                                            <p><strong>Objective:</strong> <?= h($c['research_objective'] ?? 'N/A') ?></p>
                                            <p><strong>Background / Rationale:</strong> <?= h($c['scientific_background_or_rationale'] ?? 'N/A') ?></p>
                                        </div>

                                        <div class="mb-4 border rounded p-3 bg-light">
                                            <div class="d-flex justify-content-between align-items-center mb-3">
                                                <h5 class="h6 text-uppercase text-dark fw-bold mb-0">2. Questions &amp; Hypotheses (Canonical Instantiation)</h5>
                                                <button type="button" class="btn btn-sm btn-primary" data-bs-toggle="modal" data-bs-target="#promoteItemsModal">
                                                    ⭐ Promote to Project Tables &rarr;
                                                </button>
                                            </div>

                                            <p class="mb-2"><strong>Primary Question:</strong> <span class="text-dark"><?= h($c['primary_research_question'] ?? 'N/A') ?></span></p>
                                            
                                            <?php if (!empty($c['secondary_research_questions'])): ?>
                                                <div class="mt-2"><strong>Secondary Questions:</strong></div>
                                                <ul class="mb-2 ps-3 small text-secondary">
                                                    <?php foreach ($c['secondary_research_questions'] as $sq): ?>
                                                        <li><?= h($sq) ?></li>
                                                    <?php endforeach; ?>
                                                </ul>
                                            <?php endif; ?>

                                            <?php if (!empty($c['candidate_hypotheses'])): ?>
                                                <div class="mt-2"><strong>Candidate Hypotheses:</strong></div>
                                                <ul class="mb-0 ps-3 small text-secondary">
                                                    <?php foreach ($c['candidate_hypotheses'] as $ch): ?>
                                                        <li><?= h($ch) ?></li>
                                                    <?php endforeach; ?>
                                                </ul>
                                            <?php endif; ?>
                                        </div>

                                        <div class="mb-4">
                                            <h5 class="h6 text-uppercase text-muted fw-bold">3. Strategy & Analytical Stages</h5>
                                            <p><strong>Strategy:</strong> <?= h($c['proposed_research_strategy'] ?? 'N/A') ?></p>
                                            <?php if (!empty($c['proposed_analytical_stages'])): ?>
                                                <div><strong>Analytical Stages:</strong></div>
                                                <ol>
                                                    <?php foreach ($c['proposed_analytical_stages'] as $stage): ?>
                                                        <li><?= h($stage) ?></li>
                                                    <?php endforeach; ?>
                                                </ol>
                                            <?php endif; ?>
                                        </div>

                                        <div class="mb-4">
                                            <h5 class="h6 text-uppercase text-muted fw-bold">4. Data & Confounders</h5>
                                            <p><strong>Available Data:</strong> <?= implode(', ', array_map('h', $c['available_data'] ?? [])) ?: 'N/A' ?></p>
                                            <p><strong>Potential Confounders:</strong> <?= implode(', ', array_map('h', $c['potential_confounders'] ?? [])) ?: 'N/A' ?></p>
                                            <p><strong>Sources of Bias:</strong> <?= implode(', ', array_map('h', $c['sources_of_bias'] ?? [])) ?: 'N/A' ?></p>
                                        </div>

                                        <div class="mb-4">
                                            <h5 class="h6 text-uppercase text-muted fw-bold">5. Validation & Next Steps</h5>
                                            <p><strong>Validation Strategy:</strong> <?= h($c['validation_or_robustness_strategy'] ?? 'N/A') ?></p>
                                            <p><strong>Recommended Next Step:</strong> <?= h($c['recommended_next_step'] ?? 'N/A') ?></p>
                                        </div>
                                    </div>
                                </div>

                                <!-- AI Revision Modal -->
                                <div class="modal fade" id="revisePlanModal" tabindex="-1" aria-hidden="true">
                                    <div class="modal-dialog">
                                        <div class="modal-content">
                                            <form method="post" action="research_plans.php?project_id=<?= $projectId ?>">
                                                <input type="hidden" name="action" value="revise_plan">
                                                <input type="hidden" name="project_id" value="<?= $projectId ?>">
                                                <input type="hidden" name="plan_id" value="<?= (int)$selectedPlan['id'] ?>">

                                                <div class="modal-header">
                                                    <h5 class="modal-title">AI-Assisted Plan Revision</h5>
                                                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                                                </div>
                                                <div class="modal-body">
                                                    <p class="small text-muted">Provide instructions for how the AI Scientist should refine this plan (e.g. "Reduce scope", "Focus more strongly on taxonomy"). This will create Plan v<?= (int)$selectedPlan['version'] + 1 ?>.</p>
                                                    <div class="mb-3">
                                                        <label class="form-label fw-semibold">Steering Instructions</label>
                                                        <textarea name="steering_instructions" class="form-control" rows="4" placeholder="e.g. Add molecular validation as an optional secondary objective..." required></textarea>
                                                    </div>
                                                </div>
                                                <div class="modal-footer">
                                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                                    <button type="submit" class="btn btn-primary">Generate Revision (v<?= (int)$selectedPlan['version'] + 1 ?>)</button>
                                                </div>
                                            </form>
                                        </div>
                                    </div>
                                </div>
                            <?php endif; ?>
                        </div>
                    </div>

                <?php endif; ?>

            </main>
        </div>
    </div>

<?php endif; ?>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js"></script>

<!-- Promote Questions & Hypotheses Modal -->
<div class="modal fade" id="promoteItemsModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <form method="post" action="research_plans.php?project_id=<?= $projectId ?>">
                <input type="hidden" name="action" value="promote_plan">
                <input type="hidden" name="project_id" value="<?= $projectId ?>">
                <input type="hidden" name="plan_id" value="<?= (int)$selectedPlan['id'] ?>">

                <div class="modal-header bg-primary text-white">
                    <h5 class="modal-title">Instantiate Canonical Questions &amp; Hypotheses</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <p class="small text-muted mb-3">
                        Select the questions and hypotheses from <strong>Plan v<?= (int)$selectedPlan['version'] ?></strong> that you wish to instantiate as authoritative canonical rows in the <code>research_question</code> and <code>hypothesis</code> tables.
                    </p>

                    <h6 class="fw-bold text-dark border-bottom pb-1 mb-2">Select Questions to Instantiate:</h6>
                    <div class="form-check mb-2">
                        <input class="form-check-input" type="checkbox" name="questions[]" value="0" id="q_primary" checked>
                        <label class="form-check-label fw-semibold" for="q_primary">
                            [Primary] <?= h($c['primary_research_question'] ?? '') ?>
                        </label>
                    </div>
                    <?php 
                    $qIdx = 1;
                    foreach ($c['secondary_research_questions'] ?? [] as $sq): 
                    ?>
                        <div class="form-check mb-2">
                            <input class="form-check-input" type="checkbox" name="questions[]" value="<?= $qIdx ?>" id="q_<?= $qIdx ?>" checked>
                            <label class="form-check-label small text-dark" for="q_<?= $qIdx ?>">
                                [Secondary] <?= h($sq) ?>
                            </label>
                        </div>
                    <?php 
                    $qIdx++;
                    endforeach; 
                    ?>

                    <h6 class="fw-bold text-dark border-bottom pb-1 mb-2 mt-4">Select Hypotheses to Instantiate:</h6>
                    <?php 
                    $hIdx = 0;
                    foreach ($c['candidate_hypotheses'] ?? [] as $ch): 
                    ?>
                        <div class="form-check mb-2">
                            <input class="form-check-input" type="checkbox" name="hypotheses[]" value="<?= $hIdx ?>" id="h_<?= $hIdx ?>" checked>
                            <label class="form-check-label small text-dark" for="h_<?= $hIdx ?>">
                                <?= h($ch) ?>
                            </label>
                        </div>
                    <?php 
                    $hIdx++;
                    endforeach; 
                    ?>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn btn-primary">Instantiate Selected Items</button>
                </div>
            </form>
        </div>
    </div>
</div>

</body>
</html>
