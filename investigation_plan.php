<?php

declare(strict_types=1);

require_once __DIR__ . '/includes/api.php';
require_once __DIR__ . '/includes/functions.php';

$projectId = 0;
$project = null;
$questions = [];
$selectedQuestionId = 0;
$selectedQuestion = null;
$generations = [];
$selectedGenerationId = 0;
$steps = [];
$dagData = null;
$error = null;
$flashSuccess = null;
$plans = [];
$approvedPlan = null;

try {
    $projectId = getRequiredPositiveInt('project_id');
    $project = api_get('/projects/' . $projectId);

    // Fetch questions for this project
    $allQuestions = api_get('/projects/' . $projectId . '/questions');
    $questions = is_array($allQuestions) ? $allQuestions : [];

    // Fetch research plans
    $allPlans = api_get('/projects/' . $projectId . '/research-plans');
    $plans = is_array($allPlans) ? $allPlans : [];
    foreach ($plans as $p) {
        if (($p['status'] ?? '') === 'approved') {
            $approvedPlan = $p;
            break;
        }
    }
    if (!$approvedPlan && !empty($plans)) {
        $approvedPlan = $plans[0];
    }

    if (!empty($questions)) {
        $qIdParam = isset($_GET['question_id']) ? (int)$_GET['question_id'] : 0;
        if ($qIdParam > 0) {
            foreach ($questions as $q) {
                if ((int)$q['id'] === $qIdParam) {
                    $selectedQuestionId = $qIdParam;
                    $selectedQuestion = $q;
                    break;
                }
            }
        }
        if ($selectedQuestionId === 0 && !empty($questions)) {
            $selectedQuestionId = (int)$questions[0]['id'];
            $selectedQuestion = $questions[0];
        }
    }

    if (isset($_GET['gen_id'])) {
        $selectedGenerationId = (int)$_GET['gen_id'];
    }

    // Handle POST Actions
    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        $action = trim($_POST['action'] ?? '');
        $stepId = (int)($_POST['step_id'] ?? 0);

        if ($action === 'generate_plan' && $selectedQuestionId > 0) {
            $guidance = trim($_POST['user_guidance'] ?? '');
            $focus = trim($_POST['focus_areas'] ?? '');
            $focusList = array_filter(array_map('trim', explode("\n", $focus)));
            $planIdToUse = isset($_POST['research_plan_id']) && (int)$_POST['research_plan_id'] > 0 
                ? (int)$_POST['research_plan_id'] 
                : ($approvedPlan ? (int)$approvedPlan['id'] : null);

            $payload = [
                'research_plan_id' => $planIdToUse,
                'user_guidance' => $guidance !== '' ? $guidance : null,
                'focus_areas' => !empty($focusList) ? array_values($focusList) : null,
            ];

            $res = api_post('/questions/' . $selectedQuestionId . '/investigation-plan/generate', $payload);
            $newGenId = $res['id'] ?? 0;
            header('Location: investigation_plan.php?project_id=' . $projectId . '&question_id=' . $selectedQuestionId . '&gen_id=' . $newGenId . '&generated=1');
            exit;
        }

        if ($action === 'update_step_status' && $stepId > 0) {
            $newStatus = trim($_POST['new_status'] ?? '');
            if ($newStatus !== '') {
                api_patch('/investigation-steps/' . $stepId, [
                    'status' => $newStatus,
                ]);
                header('Location: investigation_plan.php?project_id=' . $projectId . '&question_id=' . $selectedQuestionId . '&updated=1');
                exit;
            }
        }

        if ($action === 'delete_step' && $stepId > 0) {
            api_delete('/investigation-steps/' . $stepId);
            header('Location: investigation_plan.php?project_id=' . $projectId . '&question_id=' . $selectedQuestionId . '&deleted=1');
            exit;
        }

        if ($action === 'create_step' && $selectedQuestionId > 0) {
            $payload = [
                'title' => trim($_POST['title'] ?? 'New Investigation Step'),
                'scientific_goal' => trim($_POST['scientific_goal'] ?? ''),
                'rationale' => trim($_POST['rationale'] ?? ''),
                'step_type' => trim($_POST['step_type'] ?? 'data_assessment'),
                'requires_capability' => !empty($_POST['requires_capability']),
                'requires_experiment' => !empty($_POST['requires_experiment']),
                'required_operation' => trim($_POST['required_operation'] ?? '') ?: null,
                'expected_evidence' => trim($_POST['expected_evidence'] ?? '') ?: null,
                'completion_criteria' => trim($_POST['completion_criteria'] ?? '') ?: null,
                'display_order' => (int)($_POST['display_order'] ?? 1),
                'status' => 'proposed',
                'prerequisite_step_ids' => [],
            ];
            api_post('/questions/' . $selectedQuestionId . '/investigation-steps', $payload);
            header('Location: investigation_plan.php?project_id=' . $projectId . '&question_id=' . $selectedQuestionId . '&created=1');
            exit;
        }

        if ($action === 'add_dependency' && $stepId > 0) {
            $dependsOnId = (int)($_POST['depends_on_step_id'] ?? 0);
            if ($dependsOnId > 0) {
                api_post('/investigation-steps/' . $stepId . '/dependencies?depends_on_step_id=' . $dependsOnId, []);
                header('Location: investigation_plan.php?project_id=' . $projectId . '&question_id=' . $selectedQuestionId . '&dep_added=1');
                exit;
            }
        }

        if ($action === 'remove_dependency' && $stepId > 0) {
            $dependsOnId = (int)($_POST['depends_on_step_id'] ?? 0);
            if ($dependsOnId > 0) {
                api_delete('/investigation-steps/' . $stepId . '/dependencies/' . $dependsOnId);
                header('Location: investigation_plan.php?project_id=' . $projectId . '&question_id=' . $selectedQuestionId . '&dep_removed=1');
                exit;
            }
        }

        if ($action === 'match_capabilities_all' && $selectedQuestionId > 0) {
            api_post('/questions/' . $selectedQuestionId . '/capability-selection/match-all', []);
            header('Location: investigation_plan.php?project_id=' . $projectId . '&question_id=' . $selectedQuestionId . '&caps_matched=1');
            exit;
        }

        if ($action === 'match_step_capability' && $stepId > 0) {
            api_post('/investigation-steps/' . $stepId . '/capability-selection/match', []);
            header('Location: investigation_plan.php?project_id=' . $projectId . '&question_id=' . $selectedQuestionId . '&cap_matched=1');
            exit;
        }

        if ($action === 'override_capability' && $stepId > 0) {
            $capId = filter_input(INPUT_POST, 'selected_capability_id', FILTER_VALIDATE_INT) ?: null;
            $rat = trim($_POST['scientific_rationale'] ?? 'Researcher manual assignment');
            $stat = trim($_POST['researcher_status'] ?? 'override');

            api_put('/investigation-steps/' . $stepId . '/capability-selection/override', [
                'selected_capability_id' => $capId,
                'scientific_rationale' => $rat,
                'researcher_status' => $stat,
            ]);
            header('Location: investigation_plan.php?project_id=' . $projectId . '&question_id=' . $selectedQuestionId . '&cap_overridden=1');
            exit;
        }

        if ($action === 'plan_experiment' && $stepId > 0) {
            $userGuidance = trim($_POST['user_guidance'] ?? '');
            api_post('/investigation-steps/' . $stepId . '/experiments/plan', [
                'user_guidance' => $userGuidance !== '' ? $userGuidance : null,
            ]);
            header('Location: investigation_plan.php?project_id=' . $projectId . '&question_id=' . $selectedQuestionId . '&exp_planned=1');
            exit;
        }

        if ($action === 'approve_experiment') {
            $planId = (int)($_POST['plan_id'] ?? 0);
            if ($planId > 0) {
                api_post('/experiments/' . $planId . '/approve', []);
                header('Location: investigation_plan.php?project_id=' . $projectId . '&question_id=' . $selectedQuestionId . '&exp_approved=1');
                exit;
            }
        }
    }

    if (isset($_GET['generated'])) {
        $flashSuccess = 'Investigation plan successfully generated and decomposed into an explicit scientific DAG!';
    } elseif (isset($_GET['updated'])) {
        $flashSuccess = 'Investigation step status updated successfully.';
    } elseif (isset($_GET['created'])) {
        $flashSuccess = 'New investigation step added successfully.';
    } elseif (isset($_GET['deleted'])) {
        $flashSuccess = 'Investigation step deleted/archived successfully.';
    } elseif (isset($_GET['dep_added'])) {
        $flashSuccess = 'Dependency prerequisite edge added successfully.';
    } elseif (isset($_GET['dep_removed'])) {
        $flashSuccess = 'Dependency edge removed successfully.';
    } elseif (isset($_GET['caps_matched'])) {
        $flashSuccess = 'Capability matching completed across all active investigation steps!';
    } elseif (isset($_GET['cap_matched'])) {
        $flashSuccess = 'Scientific capability matched for this step.';
    } elseif (isset($_GET['cap_overridden'])) {
        $flashSuccess = 'Capability selection updated / overridden successfully.';
    } elseif (isset($_GET['exp_planned'])) {
        $flashSuccess = 'Experiment pre-specification successfully planned via AI reasoning!';
    } elseif (isset($_GET['exp_approved'])) {
        $flashSuccess = 'Experiment approved and frozen for computational execution.';
    }

    // Load Capabilities & Gaps
    $allCapabilities = api_get('/capabilities');
    $allCapabilities = is_array($allCapabilities) ? $allCapabilities : [];

    $capabilityGaps = api_get('/projects/' . $projectId . '/capability-gaps');
    $capabilityGaps = is_array($capabilityGaps) ? $capabilityGaps : [];

    // Load Generations, Steps & Analysis Plans
    $plansByStepId = [];
    if ($selectedQuestionId > 0) {
        $generations = api_get('/questions/' . $selectedQuestionId . '/investigation-plan/generations');
        $generations = is_array($generations) ? $generations : [];

        $stepsQuery = '/questions/' . $selectedQuestionId . '/investigation-steps';
        if ($selectedGenerationId > 0) {
            $stepsQuery .= '?generation_id=' . $selectedGenerationId;
        }
        $steps = api_get($stepsQuery);
        $steps = is_array($steps) ? $steps : [];

        $dagData = api_get('/questions/' . $selectedQuestionId . '/investigation-steps/dag');

        $questionPlans = api_get('/questions/' . $selectedQuestionId . '/experiments');
        if (is_array($questionPlans)) {
            foreach ($questionPlans as $qp) {
                $sId = $qp['assumptions']['investigation_step_id'] ?? null;
                if ($sId) {
                    $plansByStepId[(int)$sId] = $qp;
                }
            }
        }
    }

} catch (Throwable $e) {
    $error = $e->getMessage();
}

$pageTitle = 'Investigation Plan & Step Sequencing — ' . ($project['title'] ?? 'AI Scientist');
$activePage = 'investigation_plan';

require_once __DIR__ . '/includes/headers.php';
require_once __DIR__ . '/includes/navbar.php';

?>

<?php if ($error !== null && $project === null): ?>
    <div class="container py-5">
        <div class="alert alert-danger">
            <h1 class="h5"><i class="bi bi-exclamation-triangle-fill me-2"></i>Unable to open investigation plan</h1>
            <p class="mb-3"><?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?></p>
            <a href="projects.php" class="btn btn-outline-danger">Back to projects</a>
        </div>
    </div>
<?php else: ?>

<div class="container-fluid">
    <!-- Project Header -->
    <div class="row border-bottom bg-white">
        <div class="col-12 px-4 py-3">
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <div class="text-muted small mb-1">Research Project #<?= (int)$project['id'] ?></div>
                    <h1 class="h4 mb-1"><?= htmlspecialchars($project['title'], ENT_QUOTES, 'UTF-8') ?></h1>
                    <?php if (!empty($project['objective'])): ?>
                        <div class="text-muted small mt-1">
                            <i class="bi bi-card-text text-primary me-1"></i><?= htmlspecialchars($project['objective'], ENT_QUOTES, 'UTF-8') ?>
                        </div>
                    <?php endif; ?>
                </div>
                <div class="d-flex gap-2 align-items-center">
                    <a href="help/investigation_planning.php?project_id=<?= $projectId ?>" class="btn btn-sm btn-outline-info text-dark">
                        📖 User Guide &amp; Spec
                    </a>
                    <a href="project.php?project_id=<?= $projectId ?>" class="btn btn-sm btn-outline-secondary">Project overview</a>
                </div>
            </div>
        </div>
    </div>

    <div class="row">
        <?php require_once __DIR__ . '/includes/menu.php'; ?>

        <main class="col-md-9 col-lg-10 p-4">

            <?php if ($error): ?>
                <div class="alert alert-danger alert-dismissible fade show" role="alert">
                    <strong>Error:</strong> <?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            <?php endif; ?>

            <?php if ($flashSuccess): ?>
                <div class="alert alert-success alert-dismissible fade show" role="alert">
                    <i class="bi bi-check-circle me-1"></i> <?= htmlspecialchars($flashSuccess, ENT_QUOTES, 'UTF-8') ?>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            <?php endif; ?>

            <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-2 pb-3 mb-3 border-bottom">
                <div>
                    <h1 class="h2 mb-1">
                        <i class="bi bi-diagram-3 text-primary me-2"></i>Investigation Planning & Scientific Step Sequencing
                    </h1>
                    <p class="text-muted mb-0">
                        Bridge strategic research plans into explicit, non-prescriptive Directed Acyclic Graphs (DAG) of InvestigationSteps.
                    </p>
                </div>
                <div class="btn-toolbar mb-2 mb-md-0 gap-2">
                    <a href="help/investigation_planning.php?project_id=<?= $projectId ?>" class="btn btn-outline-primary">
                        <i class="bi bi-question-circle me-1"></i>Guide: DAG Workflow
                    </a>
                    <?php if ($selectedQuestionId > 0 && !empty($steps)): ?>
                        <form method="post" action="investigation_plan.php?project_id=<?= $projectId ?>&question_id=<?= $selectedQuestionId ?>" class="d-inline">
                            <input type="hidden" name="action" value="match_capabilities_all">
                            <button type="submit" class="btn btn-outline-success" title="Run Capability Matching across all active steps">
                                <i class="bi bi-cpu me-1"></i> Match Capabilities with AI
                            </button>
                        </form>
                    <?php endif; ?>
                    <?php if ($selectedQuestionId > 0): ?>
                        <button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#generatePlanModal">
                            <i class="bi bi-diagram-3-fill me-1"></i> Generate Investigation DAG with AI
                        </button>
                        <button type="button" class="btn btn-outline-secondary" data-bs-toggle="modal" data-bs-target="#createStepModal">
                            <i class="bi bi-plus-lg me-1"></i> Add Manual Step
                        </button>
                    <?php endif; ?>
                </div>
            </div>


            <!-- Question & Generation Selector Toolbar -->
            <div class="card bg-light border-0 mb-4 shadow-sm">
                <div class="card-body p-3">
                    <div class="row align-items-center g-3">
                        <div class="col-md-6">
                            <label class="form-label small fw-semibold text-uppercase text-muted mb-1">Focal Research Question</label>
                            <form method="get" action="investigation_plan.php" class="d-flex gap-2">
                                <input type="hidden" name="project_id" value="<?= $projectId ?>">
                                <select name="question_id" class="form-select" onchange="this.form.submit()">
                                    <?php if (empty($questions)): ?>
                                        <option value="">No canonical research questions found for this project</option>
                                    <?php else: ?>
                                        <?php foreach ($questions as $q): ?>
                                            <option value="<?= $q['id'] ?>" <?= $selectedQuestionId === (int)$q['id'] ? 'selected' : '' ?>>
                                                Q<?= $q['id'] ?>: <?= htmlspecialchars(mb_strimwidth($q['question'], 0, 90, '...'), ENT_QUOTES, 'UTF-8') ?>
                                            </option>
                                        <?php endforeach; ?>
                                    <?php endif; ?>
                                </select>
                            </form>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label small fw-semibold text-uppercase text-muted mb-1">Generation Batch Filter</label>
                            <form method="get" action="investigation_plan.php" class="d-flex gap-2">
                                <input type="hidden" name="project_id" value="<?= $projectId ?>">
                                <input type="hidden" name="question_id" value="<?= $selectedQuestionId ?>">
                                <select name="gen_id" class="form-select" onchange="this.form.submit()">
                                    <option value="0">All Active Steps (Combined DAG)</option>
                                    <?php foreach ($generations as $idx => $g): ?>
                                        <option value="<?= $g['id'] ?>" <?= $selectedGenerationId === (int)$g['id'] ? 'selected' : '' ?>>
                                            Batch #<?= $g['id'] ?> (<?= date('M j, H:i', strtotime($g['created_at'])) ?>) &mdash; <?= $g['steps_count'] ?? 0 ?> steps
                                        </option>
                                    <?php endforeach; ?>
                                </select>
                            </form>
                        </div>
                        <div class="col-md-2 text-md-end">
                            <label class="form-label small fw-semibold text-uppercase text-muted mb-1">Active Research Plan</label>
                            <div>
                                <?php if ($approvedPlan): ?>
                                    <span class="badge bg-success-subtle text-success border border-success-subtle p-2">
                                        <i class="bi bi-file-earmark-check me-1"></i>Plan v<?= $approvedPlan['version'] ?> (<?= ucfirst($approvedPlan['status']) ?>)
                                    </span>
                                <?php else: ?>
                                    <span class="badge bg-warning-subtle text-warning border border-warning-subtle p-2">
                                        No Plan Approved
                                    </span>
                                <?php endif; ?>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <?php if ($selectedQuestion): ?>
                <!-- Question Context Card -->
                <div class="card mb-4 border-start border-primary border-4 shadow-sm">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <span class="badge bg-primary mb-2">Question Q<?= $selectedQuestion['id'] ?></span>
                                <h4 class="card-title fw-bold text-dark mb-1">
                                    <?= htmlspecialchars($selectedQuestion['question'], ENT_QUOTES, 'UTF-8') ?>
                                </h4>
                                <?php if (!empty($selectedQuestion['notes'])): ?>
                                    <p class="text-muted mb-0 small mt-1"><?= nl2br(htmlspecialchars($selectedQuestion['notes'], ENT_QUOTES, 'UTF-8')) ?></p>
                                <?php endif; ?>
                            </div>
                            <div class="d-flex gap-2">
                                <?php
                                    $totalSteps = count($steps);
                                    $approvedCount = 0;
                                    $completedCount = 0;
                                    $blockedCount = 0;
                                    foreach ($steps as $st) {
                                        if ($st['status'] === 'approved') $approvedCount++;
                                        if ($st['status'] === 'completed') $completedCount++;
                                        if (!empty($st['is_blocked'])) $blockedCount++;
                                    }
                                ?>
                                <div class="text-center px-2 py-1 bg-light rounded border">
                                    <div class="small text-muted">Total</div>
                                    <div class="fw-bold fs-5"><?= $totalSteps ?></div>
                                </div>
                                <div class="text-center px-2 py-1 bg-light rounded border">
                                    <div class="small text-muted">Approved</div>
                                    <div class="fw-bold fs-5 text-primary"><?= $approvedCount ?></div>
                                </div>
                                <div class="text-center px-2 py-1 bg-light rounded border">
                                    <div class="small text-muted">Completed</div>
                                    <div class="fw-bold fs-5 text-success"><?= $completedCount ?></div>
                                </div>
                                <div class="text-center px-2 py-1 bg-light rounded border">
                                    <div class="small text-muted">Blocked</div>
                                    <div class="fw-bold fs-5 text-danger"><?= $blockedCount ?></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Latest Generation Rationale & Uncertainties (if available) -->
                <?php 
                    $activeGen = null;
                    if ($selectedGenerationId > 0) {
                        foreach ($generations as $g) {
                            if ((int)$g['id'] === $selectedGenerationId) {
                                $activeGen = $g;
                                break;
                            }
                        }
                    } elseif (!empty($generations)) {
                        $activeGen = $generations[0];
                    }
                ?>
                <?php if ($activeGen && !empty($activeGen['summary_rationale'])): ?>
                    <div class="card mb-4 border-0 shadow-sm bg-light-subtle">
                        <div class="card-header bg-transparent border-bottom d-flex justify-content-between align-items-center">
                            <span class="fw-semibold text-secondary">
                                <i class="bi bi-lightbulb text-warning me-1"></i> Generation Synthesis Rationale (Batch #<?= $activeGen['id'] ?>)
                            </span>
                            <span class="badge bg-secondary-subtle text-secondary small">
                                Model: <?= htmlspecialchars($activeGen['model_provenance']['model'] ?? 'LLM Gateway', ENT_QUOTES, 'UTF-8') ?>
                            </span>
                        </div>
                        <div class="card-body">
                            <p class="card-text text-secondary mb-3">
                                <?= nl2br(htmlspecialchars($activeGen['summary_rationale'], ENT_QUOTES, 'UTF-8')) ?>
                            </p>
                            <?php if (!empty($activeGen['identified_uncertainties'])): ?>
                                <div class="mt-2 pt-2 border-top">
                                    <div class="small fw-semibold text-muted text-uppercase mb-1">
                                        <i class="bi bi-exclamation-triangle text-warning me-1"></i> Identified Methodological Uncertainties & Risks:
                                    </div>
                                    <ul class="mb-0 small text-muted">
                                        <?php foreach ($activeGen['identified_uncertainties'] as $unc): ?>
                                            <li><?= htmlspecialchars((string)$unc, ENT_QUOTES, 'UTF-8') ?></li>
                                        <?php endforeach; ?>
                                    </ul>
                                </div>
                            <?php endif; ?>
                        </div>
                    </div>
                <?php endif; ?>

                <!-- Investigation Steps List & DAG Cards -->
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h4 class="h5 fw-bold mb-0">
                        <i class="bi bi-list-task me-2 text-primary"></i>Investigation Steps (Workflow Sequence)
                    </h4>
                    <span class="text-muted small">Dependencies are authoritative; display order organizes cards</span>
                </div>

                <?php if (empty($steps)): ?>
                    <div class="card text-center p-5 border-dashed">
                        <div class="py-4">
                            <i class="bi bi-diagram-3 text-muted display-4"></i>
                            <h5 class="mt-3 text-secondary">No Investigation Steps Found</h5>
                            <p class="text-muted max-w-md mx-auto">
                                Click <strong>Generate Plan with AI</strong> to decompose this Research Question into a grounded, multi-stage scientific DAG.
                            </p>
                            <button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#generatePlanModal">
                                <i class="bi bi-cpu me-1"></i> Generate Plan with AI
                            </button>
                        </div>
                    </div>
                <?php else: ?>
                    <div class="row g-3 mb-5">
                        <?php foreach ($steps as $idx => $st): ?>
                            <?php
                                $statusClass = 'bg-secondary';
                                if ($st['status'] === 'approved') $statusClass = 'bg-primary';
                                elseif ($st['status'] === 'in_progress') $statusClass = 'bg-info text-dark';
                                elseif ($st['status'] === 'completed') $statusClass = 'bg-success';
                                elseif ($st['status'] === 'skipped') $statusClass = 'bg-warning text-dark';
                                elseif ($st['status'] === 'rejected') $statusClass = 'bg-danger';

                                $typeBg = 'bg-light text-dark';
                                if (in_array($st['step_type'], ['taxonomy', 'molecular_validation', 'phylogenetic_analysis'])) $typeBg = 'bg-success-subtle text-success';
                                elseif (in_array($st['step_type'], ['representation', 'model_training'])) $typeBg = 'bg-primary-subtle text-primary';
                                elseif (in_array($st['step_type'], ['statistical_analysis', 'robustness'])) $typeBg = 'bg-info-subtle text-info-emphasis';
                                elseif (in_array($st['step_type'], ['evidence_synthesis', 'expert_review'])) $typeBg = 'bg-purple-subtle text-purple';
                            ?>
                            <div class="col-12" id="step-<?= $st['id'] ?>">
                                <div class="card shadow-sm border <?= !empty($st['is_blocked']) ? 'border-danger-subtle' : ($st['status'] === 'approved' ? 'border-primary-subtle' : '') ?>">
                                    <div class="card-header bg-white d-flex justify-content-between align-items-center py-2">
                                        <div class="d-flex align-items-center gap-2">
                                            <span class="badge bg-dark text-white fw-bold px-2 py-1">Step #<?= $st['id'] ?></span>
                                            <span class="badge <?= $typeBg ?> border px-2 py-1"><?= htmlspecialchars(str_replace('_', ' ', $st['step_type']), ENT_QUOTES, 'UTF-8') ?></span>
                                            
                                            <!-- Computed Multi-Factor Readiness Badge -->
                                            <?php 
                                                $rState = $st['readiness_state'] ?? (!empty($st['is_blocked']) ? 'dependency_blocked' : 'ready');
                                            ?>
                                            <?php if ($rState === 'dependency_blocked'): ?>
                                                <span class="badge bg-warning-subtle text-warning-emphasis border border-warning-subtle" title="Blocked: Prerequisite steps are not completed yet">
                                                    <i class="bi bi-lock-fill me-1"></i>Prerequisite Blocked
                                                </span>
                                            <?php elseif ($rState === 'capability_blocked'): ?>
                                                <span class="badge bg-danger-subtle text-danger border border-danger-subtle" title="Blocked: No registered capability matched or Capability Gap exists">
                                                    <i class="bi bi-exclamation-octagon-fill me-1"></i>Capability Blocked
                                                </span>
                                            <?php else: ?>
                                                <span class="badge bg-success-subtle text-success border border-success-subtle" title="All prerequisites satisfied & capability matched">
                                                    <i class="bi bi-unlock-fill me-1"></i>Ready
                                                </span>
                                            <?php endif; ?>

                                            <!-- Capability & Experiment Indicators -->
                                            <?php if (!empty($st['selected_capability_display_name'])): ?>
                                                <button type="button" class="btn btn-sm btn-outline-primary py-0 px-2 fw-semibold" data-bs-toggle="modal" data-bs-target="#capModal-<?= $st['id'] ?>" title="View / Override Matched Capability">
                                                    <i class="bi bi-cpu-fill me-1"></i><?= htmlspecialchars($st['selected_capability_display_name'], ENT_QUOTES, 'UTF-8') ?>
                                                </button>
                                            <?php elseif (!empty($st['has_capability_gap'])): ?>
                                                <button type="button" class="btn btn-sm btn-outline-danger py-0 px-2 fw-semibold" data-bs-toggle="modal" data-bs-target="#capModal-<?= $st['id'] ?>" title="Capability Gap Identified (Execution Blocked)">
                                                    <i class="bi bi-exclamation-triangle-fill me-1"></i>Capability Gap
                                                </button>
                                            <?php elseif (!empty($st['requires_capability'])): ?>
                                                <button type="button" class="btn btn-sm btn-outline-secondary py-0 px-2" data-bs-toggle="modal" data-bs-target="#capModal-<?= $st['id'] ?>" title="Requires registered capability">
                                                    <i class="bi bi-tools me-1"></i>Unmatched Capability
                                                </button>
                                            <?php endif; ?>

                                            <?php if (!empty($st['requires_experiment'])): ?>
                                                <span class="badge bg-indigo-subtle text-primary border" title="Requires empirical/computational experiment run">
                                                    <i class="bi bi-flask me-1"></i>Experiment Run
                                                </span>
                                            <?php endif; ?>
                                        </div>

                                        <div class="d-flex align-items-center gap-2">
                                            <!-- Lifecycle Status Dropdown -->
                                            <form method="post" action="investigation_plan.php?project_id=<?= $projectId ?>&question_id=<?= $selectedQuestionId ?>" class="d-inline">
                                                <input type="hidden" name="action" value="update_step_status">
                                                <input type="hidden" name="step_id" value="<?= $st['id'] ?>">
                                                <select name="new_status" class="form-select form-select-sm fw-semibold" onchange="this.form.submit()">
                                                    <option value="proposed" <?= $st['status'] === 'proposed' ? 'selected' : '' ?>>Proposed</option>
                                                    <option value="approved" <?= $st['status'] === 'approved' ? 'selected' : '' ?>>Approved</option>
                                                    <option value="in_progress" <?= $st['status'] === 'in_progress' ? 'selected' : '' ?>>In Progress</option>
                                                    <option value="completed" <?= $st['status'] === 'completed' ? 'selected' : '' ?>>Completed</option>
                                                    <option value="skipped" <?= $st['status'] === 'skipped' ? 'selected' : '' ?>>Skipped</option>
                                                    <option value="rejected" <?= $st['status'] === 'rejected' ? 'selected' : '' ?>>Rejected</option>
                                                </select>
                                            </form>
                                                    <option value="rejected" <?= $st['status'] === 'rejected' ? 'selected' : '' ?>>Rejected</option>
                                                </select>
                                            </form>

                                            <!-- Step Action Buttons -->
                                            <button type="button" class="btn btn-sm btn-outline-secondary" data-bs-toggle="modal" data-bs-target="#depModal-<?= $st['id'] ?>" title="Manage Dependencies">
                                                <i class="bi bi-link-45deg"></i>
                                            </button>
                                            <form method="post" action="investigation_plan.php?project_id=<?= $projectId ?>&question_id=<?= $selectedQuestionId ?>" class="d-inline" onsubmit="return confirm('Archive/delete this investigation step?');">
                                                <input type="hidden" name="action" value="delete_step">
                                                <input type="hidden" name="step_id" value="<?= $st['id'] ?>">
                                                <button type="submit" class="btn btn-sm btn-outline-danger" title="Delete or Archive Step">
                                                    <i class="bi bi-trash"></i>
                                                </button>
                                            </form>
                                        </div>
                                    </div>

                                    <div class="card-body">
                                        <h5 class="card-title fw-bold text-dark mb-2">
                                            <?= htmlspecialchars($st['title'], ENT_QUOTES, 'UTF-8') ?>
                                        </h5>
                                        <p class="text-secondary mb-3">
                                            <strong>Goal:</strong> <?= htmlspecialchars($st['scientific_goal'], ENT_QUOTES, 'UTF-8') ?>
                                        </p>

                                        <div class="row g-3 small text-muted">
                                            <div class="col-md-6">
                                                <div class="p-2 bg-light rounded border h-100">
                                                    <div class="fw-semibold text-dark mb-1"><i class="bi bi-question-circle text-primary me-1"></i>Scientific Rationale:</div>
                                                    <div><?= nl2br(htmlspecialchars($st['rationale'], ENT_QUOTES, 'UTF-8')) ?></div>
                                                </div>
                                            </div>
                                            <div class="col-md-6">
                                                <div class="p-2 bg-light rounded border h-100">
                                                    <div class="fw-semibold text-dark mb-1"><i class="bi bi-check2-circle text-success me-1"></i>Completion Criteria & Expected Evidence:</div>
                                                    <div><strong>Evidence:</strong> <?= htmlspecialchars($st['expected_evidence'] ?? 'None specified', ENT_QUOTES, 'UTF-8') ?></div>
                                                    <div class="mt-1"><strong>Criteria:</strong> <?= htmlspecialchars($st['completion_criteria'] ?? 'None specified', ENT_QUOTES, 'UTF-8') ?></div>
                                                </div>
                                            </div>
                                        </div>

                                        <!-- Phase 10 Experiment Specification Block -->
                                        <?php 
                                            $boundExp = $plansByStepId[$st['id']] ?? null;
                                        ?>
                                        <?php if ($boundExp): ?>
                                            <div class="mt-3 p-3 bg-white border border-primary-subtle rounded shadow-sm">
                                                <div class="d-flex justify-content-between align-items-center mb-2">
                                                    <div class="fw-bold text-primary">
                                                        <i class="bi bi-flask-fill me-1"></i> Pre-specified Experiment: <?= htmlspecialchars($boundExp['assumptions']['working_title'] ?? ('Experiment #' . $boundExp['id']), ENT_QUOTES, 'UTF-8') ?>
                                                    </div>
                                                    <div class="d-flex align-items-center gap-2">
                                                        <span class="badge <?= $boundExp['status'] === 'approved' ? 'bg-success' : 'bg-warning text-dark' ?>">
                                                            <?= htmlspecialchars(strtoupper($boundExp['status']), ENT_QUOTES, 'UTF-8') ?>
                                                        </span>
                                                        <?php if ($boundExp['status'] !== 'approved'): ?>
                                                            <form method="post" action="investigation_plan.php?project_id=<?= $projectId ?>&question_id=<?= $selectedQuestionId ?>" class="d-inline">
                                                                <input type="hidden" name="action" value="approve_experiment">
                                                                <input type="hidden" name="plan_id" value="<?= $boundExp['id'] ?>">
                                                                <button type="submit" class="btn btn-sm btn-success py-0 px-2" title="Approve & Freeze Experiment for execution">
                                                                    <i class="bi bi-check2-circle me-1"></i>Approve
                                                                </button>
                                                            </form>
                                                        <?php endif; ?>
                                                        <button type="button" class="btn btn-sm btn-outline-primary py-0 px-2" data-bs-toggle="modal" data-bs-target="#expModal-<?= $st['id'] ?>" title="Re-plan or refine with AI">
                                                            <i class="bi bi-magic me-1"></i>Re-plan
                                                        </button>
                                                        <a href="analyses.php?project_id=<?= $projectId ?>#plan-<?= $boundExp['id'] ?>" class="btn btn-sm btn-outline-secondary py-0 px-2">
                                                            View in Analyses <i class="bi bi-arrow-up-right"></i>
                                                        </a>
                                                    </div>
                                                </div>
                                                <div class="small text-secondary mb-2">
                                                    <strong>Objective:</strong> <?= htmlspecialchars($boundExp['estimand'] ?? ($boundExp['assumptions']['scientific_objective'] ?? 'N/A'), ENT_QUOTES, 'UTF-8') ?>
                                                </div>
                                                <?php if (!empty($boundExp['parameters'])): ?>
                                                    <div class="small bg-light p-2 rounded border">
                                                        <strong>Pre-specified Parameters:</strong>
                                                        <div class="d-flex flex-wrap gap-2 mt-1">
                                                            <?php foreach ($boundExp['parameters'] as $pk => $pv): ?>
                                                                <span class="badge bg-light text-dark border">
                                                                    <code><?= htmlspecialchars((string)$pk, ENT_QUOTES, 'UTF-8') ?></code>: 
                                                                    <strong><?= htmlspecialchars(is_array($pv) ? json_encode($pv) : (string)$pv, ENT_QUOTES, 'UTF-8') ?></strong>
                                                                </span>
                                                            <?php endforeach; ?>
                                                        </div>
                                                    </div>
                                                <?php endif; ?>
                                            </div>
                                        <?php elseif (!empty($st['requires_experiment']) || !empty($st['requires_capability'])): ?>
                                            <div class="mt-3 p-2 bg-light rounded border d-flex justify-content-between align-items-center">
                                                <div class="small text-muted">
                                                    <i class="bi bi-info-circle me-1"></i> No experiment pre-specified yet for this step.
                                                </div>
                                                <button type="button" class="btn btn-sm btn-primary py-1 px-3 shadow-sm" data-bs-toggle="modal" data-bs-target="#expModal-<?= $st['id'] ?>">
                                                    <i class="bi bi-magic me-1"></i> Plan Experiment with AI (LLM Stage 4)
                                                </button>
                                            </div>
                                        <?php endif; ?>

                                        <!-- Prerequisite & Dependent Links -->
                                        <div class="mt-3 pt-2 border-top d-flex justify-content-between align-items-center small">
                                            <div>
                                                <span class="text-muted fw-semibold me-1"><i class="bi bi-arrow-left text-secondary"></i> Depends On (Prerequisites):</span>
                                                <?php if (empty($st['prerequisite_step_ids'])): ?>
                                                    <span class="badge bg-light text-muted border">None (Initial step)</span>
                                                <?php else: ?>
                                                    <?php foreach ($st['prerequisite_step_ids'] as $pid): ?>
                                                        <a href="#step-<?= $pid ?>" class="badge bg-secondary-subtle text-secondary border text-decoration-none me-1">
                                                            Step #<?= $pid ?>
                                                        </a>
                                                    <?php endforeach; ?>
                                                <?php endif; ?>
                                            </div>
                                            <div>
                                                <span class="text-muted fw-semibold me-1">Depended Upon By:</span>
                                                <?php if (empty($st['dependent_step_ids'])): ?>
                                                    <span class="badge bg-light text-muted border">None (Terminal step)</span>
                                                <?php else: ?>
                                                    <?php foreach ($st['dependent_step_ids'] as $did): ?>
                                                        <a href="#step-<?= $did ?>" class="badge bg-info-subtle text-info-emphasis border text-decoration-none me-1">
                                                            Step #<?= $did ?> <i class="bi bi-arrow-right text-secondary"></i>
                                                        </a>
                                                    <?php endforeach; ?>
                                                <?php endif; ?>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Plan Experiment with AI Modal for Step -->
                            <div class="modal fade" id="expModal-<?= $st['id'] ?>" tabindex="-1" aria-labelledby="expModalLabel-<?= $st['id'] ?>" aria-hidden="true">
                                <div class="modal-dialog modal-lg">
                                    <div class="modal-content">
                                        <form method="post" action="investigation_plan.php?project_id=<?= $projectId ?>&question_id=<?= $selectedQuestionId ?>">
                                            <input type="hidden" name="action" value="plan_experiment">
                                            <input type="hidden" name="step_id" value="<?= $st['id'] ?>">
                                            <div class="modal-header">
                                                <h5 class="modal-title" id="expModalLabel-<?= $st['id'] ?>">
                                                    <i class="bi bi-magic text-primary me-2"></i>LLM Stage 4: Plan Experiment for Step #<?= $st['id'] ?>
                                                </h5>
                                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                                            </div>
                                            <div class="modal-body">
                                                <div class="alert alert-info small mb-3">
                                                    The LLM Gateway will pre-specify the complete scientific experiment: objective, protocol, input parameters (strictly validated against registered capability schema), control strategies, replication seeds, and result interpretation criteria.
                                                </div>
                                                <div class="mb-3">
                                                    <label class="form-label fw-semibold">Step Goal</label>
                                                    <input type="text" class="form-control" value="<?= htmlspecialchars($st['scientific_goal'], ENT_QUOTES, 'UTF-8') ?>" readonly disabled>
                                                </div>
                                                <div class="mb-3">
                                                    <label class="form-label fw-semibold">Matched Capability</label>
                                                    <input type="text" class="form-control" value="<?= htmlspecialchars($st['selected_capability_display_name'] ?? 'Generic / Unbound', ENT_QUOTES, 'UTF-8') ?>" readonly disabled>
                                                </div>
                                                <div class="mb-3">
                                                    <label class="form-label fw-semibold">Researcher Guidance / Protocol Constraints (Optional)</label>
                                                    <textarea name="user_guidance" class="form-control" rows="3" placeholder="e.g. Set permutation depth to 999, use Euclidean distance, enforce provider-adjusted controls..."></textarea>
                                                </div>
                                            </div>
                                            <div class="modal-footer">
                                                <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
                                                <button type="submit" class="btn btn-primary">
                                                    <i class="bi bi-stars me-1"></i> Plan Experiment with AI
                                                </button>
                                            </div>
                                        </form>
                                    </div>
                                </div>
                            </div>

                            <!-- Manage Dependencies Modal for Step -->
                            <div class="modal fade" id="depModal-<?= $st['id'] ?>" tabindex="-1" aria-hidden="true">
                                <div class="modal-dialog">
                                    <div class="modal-content">
                                        <div class="modal-header">
                                            <h5 class="modal-title">Manage Dependencies for Step #<?= $st['id'] ?></h5>
                                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                                        </div>
                                        <div class="modal-body">
                                            <h6 class="fw-bold mb-2">Existing Prerequisites:</h6>
                                            <?php if (empty($st['prerequisite_step_ids'])): ?>
                                                <p class="text-muted small">No prerequisites currently defined.</p>
                                            <?php else: ?>
                                                <ul class="list-group mb-3">
                                                    <?php foreach ($st['prerequisite_step_ids'] as $pid): ?>
                                                        <li class="list-group-item d-flex justify-content-between align-items-center">
                                                            <span>Step #<?= $pid ?></span>
                                                            <form method="post" action="investigation_plan.php?project_id=<?= $projectId ?>&question_id=<?= $selectedQuestionId ?>" class="d-inline">
                                                                <input type="hidden" name="action" value="remove_dependency">
                                                                <input type="hidden" name="step_id" value="<?= $st['id'] ?>">
                                                                <input type="hidden" name="depends_on_step_id" value="<?= $pid ?>">
                                                                <button type="submit" class="btn btn-sm btn-outline-danger">Remove</button>
                                                            </form>
                                                        </li>
                                                    <?php endforeach; ?>
                                                </ul>
                                            <?php endif; ?>

                                            <h6 class="fw-bold mb-2">Add New Prerequisite:</h6>
                                            <form method="post" action="investigation_plan.php?project_id=<?= $projectId ?>&question_id=<?= $selectedQuestionId ?>">
                                                <input type="hidden" name="action" value="add_dependency">
                                                <input type="hidden" name="step_id" value="<?= $st['id'] ?>">
                                                <div class="input-group mb-3">
                                                    <select name="depends_on_step_id" class="form-select" required>
                                                        <option value="">Select prerequisite step...</option>
                                                        <?php foreach ($steps as $other): ?>
                                                            <?php if ($other['id'] !== $st['id'] && !in_array($other['id'], $st['prerequisite_step_ids'])): ?>
                                                                <option value="<?= $other['id'] ?>">
                                                                    Step #<?= $other['id'] ?>: <?= htmlspecialchars(mb_strimwidth($other['title'], 0, 50, '...'), ENT_QUOTES, 'UTF-8') ?>
                                                                </option>
                                                            <?php endif; ?>
                                                        <?php endforeach; ?>
                                                    </select>
                                                    <button class="btn btn-primary" type="submit">Add Edge</button>
                                                </div>
                                            </form>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Capability Selection & Override Modal for Step -->
                            <div class="modal fade" id="capModal-<?= $st['id'] ?>" tabindex="-1" aria-hidden="true">
                                <div class="modal-dialog modal-lg">
                                    <div class="modal-content">
                                        <div class="modal-header">
                                            <h5 class="modal-title">
                                                <i class="bi bi-cpu text-primary me-2"></i>Scientific Capability Selection for Step #<?= $st['id'] ?>
                                            </h5>
                                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                                        </div>
                                        <div class="modal-body">
                                            <div class="mb-3 p-3 bg-light rounded border">
                                                <h6 class="fw-bold text-dark mb-1"><?= htmlspecialchars($st['title'], ENT_QUOTES, 'UTF-8') ?></h6>
                                                <p class="text-secondary small mb-1"><strong>Goal:</strong> <?= htmlspecialchars($st['scientific_goal'], ENT_QUOTES, 'UTF-8') ?></p>
                                                <?php if (!empty($st['required_operation'])): ?>
                                                    <p class="text-secondary small mb-0"><strong>Required Operation:</strong> <?= htmlspecialchars($st['required_operation'], ENT_QUOTES, 'UTF-8') ?></p>
                                                <?php endif; ?>
                                            </div>

                                            <div class="row g-3 mb-3">
                                                <div class="col-md-6">
                                                    <div class="card h-100 border shadow-none">
                                                        <div class="card-body">
                                                            <h6 class="fw-bold text-dark mb-2"><i class="bi bi-check-circle text-success me-1"></i>Current Capability Status</h6>
                                                            <?php if (!empty($st['selected_capability_display_name'])): ?>
                                                                <div class="badge bg-primary text-white mb-2"><?= htmlspecialchars($st['selected_capability_display_name'], ENT_QUOTES, 'UTF-8') ?></div>
                                                                <div class="small text-muted mb-1"><strong>Key:</strong> <code><?= htmlspecialchars($st['selected_capability_key'] ?? '', ENT_QUOTES, 'UTF-8') ?></code></div>
                                                            <?php elseif (!empty($st['has_capability_gap'])): ?>
                                                                <div class="alert alert-danger p-2 small mb-2">
                                                                    <i class="bi bi-exclamation-triangle-fill me-1"></i><strong>Capability Gap Logged</strong>
                                                                    <div>No existing software or adapter satisfies this step.</div>
                                                                </div>
                                                            <?php else: ?>
                                                                <div class="text-muted small">No capability matched yet.</div>
                                                            <?php endif; ?>

                                                            <form method="post" action="investigation_plan.php?project_id=<?= $projectId ?>&question_id=<?= $selectedQuestionId ?>" class="mt-3">
                                                                <input type="hidden" name="action" value="match_step_capability">
                                                                <input type="hidden" name="step_id" value="<?= $st['id'] ?>">
                                                                <button type="submit" class="btn btn-sm btn-outline-primary w-100">
                                                                    <i class="bi bi-magic me-1"></i> Run AI Capability Match
                                                                </button>
                                                            </form>
                                                        </div>
                                                    </div>
                                                </div>

                                                <div class="col-md-6">
                                                    <div class="card h-100 border shadow-none">
                                                        <div class="card-body">
                                                            <h6 class="fw-bold text-dark mb-2"><i class="bi bi-sliders me-1"></i>Researcher Override / Curation</h6>
                                                            <form method="post" action="investigation_plan.php?project_id=<?= $projectId ?>&question_id=<?= $selectedQuestionId ?>">
                                                                <input type="hidden" name="action" value="override_capability">
                                                                <input type="hidden" name="step_id" value="<?= $st['id'] ?>">

                                                                <div class="mb-2">
                                                                    <label class="form-label small fw-semibold">Assign Capability:</label>
                                                                    <select name="selected_capability_id" class="form-select form-select-sm">
                                                                        <option value="">-- Flag as Capability Gap (None Adequate) --</option>
                                                                        <?php foreach ($allCapabilities as $c): ?>
                                                                            <option value="<?= $c['id'] ?>" <?= (!empty($st['selected_capability_id']) && (int)$st['selected_capability_id'] === (int)$c['id']) ? 'selected' : '' ?>>
                                                                                <?= htmlspecialchars($c['display_name'], ENT_QUOTES, 'UTF-8') ?> (<?= htmlspecialchars($c['capability_key'], ENT_QUOTES, 'UTF-8') ?>)
                                                                            </option>
                                                                        <?php endforeach; ?>
                                                                    </select>
                                                                </div>

                                                                <div class="mb-2">
                                                                    <label class="form-label small fw-semibold">Researcher Rationale:</label>
                                                                    <textarea name="scientific_rationale" class="form-control form-control-sm" rows="2" placeholder="Explain reason for assignment or override..." required>Manual assignment by researcher</textarea>
                                                                </div>

                                                                <button type="submit" class="btn btn-sm btn-success w-100">
                                                                    <i class="bi bi-check2 me-1"></i> Save Capability Decision
                                                                </button>
                                                            </form>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        <?php endforeach; ?>
                    </div>
                <?php endif; ?>

            <?php else: ?>
                <div class="alert alert-info">
                    Please select or create a research question in this project to view or generate an investigation plan.
                </div>
            <?php endif; ?>

        </main>
    </div>
</div>

<!-- Modal: Generate Plan with AI -->
<div class="modal fade" id="generatePlanModal" tabindex="-1" aria-labelledby="generatePlanModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <form method="post" action="investigation_plan.php?project_id=<?= $projectId ?>&question_id=<?= $selectedQuestionId ?>">
                <input type="hidden" name="action" value="generate_plan">
                <div class="modal-header">
                    <h5 class="modal-title" id="generatePlanModalLabel">
                        <i class="bi bi-cpu text-primary me-2"></i>Generate Investigation Plan with AI
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <p class="text-muted small">
                        The AI Scientist will synthesize the focal Research Question and approved Research Plan using grounded context, creating an explicit DAG of InvestigationSteps.
                    </p>

                    <div class="mb-3">
                        <label class="form-label fw-semibold">Research Plan to Decompose</label>
                        <select name="research_plan_id" class="form-select">
                            <?php foreach ($plans as $p): ?>
                                <option value="<?= $p['id'] ?>" <?= ($approvedPlan && $approvedPlan['id'] === $p['id']) ? 'selected' : '' ?>>
                                    Plan v<?= $p['version'] ?>: <?= htmlspecialchars($p['title'], ENT_QUOTES, 'UTF-8') ?> (<?= ucfirst($p['status']) ?>)
                                </option>
                            <?php endforeach; ?>
                        </select>
                    </div>

                    <div class="mb-3">
                        <label class="form-label fw-semibold">Researcher Guidance / Methodological Preferences (Optional)</label>
                        <textarea name="user_guidance" class="form-control" rows="3" placeholder="e.g. Focus on conchological landmarks, exclude invasive sampling, include adversarial confounder tests..."></textarea>
                    </div>

                    <div class="mb-3">
                        <label class="form-label fw-semibold">Specific Focus Areas (Optional, one per line)</label>
                        <textarea name="focus_areas" class="form-control" rows="2" placeholder="Taxonomic standardization&#10;Phenotypic clustering&#10;COX1 validation"></textarea>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn btn-primary">
                        <i class="bi bi-stars me-1"></i> Generate Investigation DAG
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>

<!-- Modal: Add Manual Step -->
<div class="modal fade" id="createStepModal" tabindex="-1" aria-labelledby="createStepModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <form method="post" action="investigation_plan.php?project_id=<?= $projectId ?>&question_id=<?= $selectedQuestionId ?>">
                <input type="hidden" name="action" value="create_step">
                <div class="modal-header">
                    <h5 class="modal-title" id="createStepModalLabel">Add Manual Investigation Step</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div class="mb-3">
                        <label class="form-label fw-semibold">Step Title</label>
                        <input type="text" name="title" class="form-control" required placeholder="e.g. Perform aperture landmark calibration">
                    </div>
                    <div class="row g-3 mb-3">
                        <div class="col-md-6">
                            <label class="form-label fw-semibold">Step Type</label>
                            <select name="step_type" class="form-select">
                                <option value="data_assessment">Data Assessment / Sampling Audit</option>
                                <option value="taxonomy">Taxonomy & Nomenclature Verification</option>
                                <option value="literature">Literature Review & Prior Claims</option>
                                <option value="representation">Representation & Feature Extraction</option>
                                <option value="statistical_analysis">Statistical Analysis & Hypothesis Testing</option>
                                <option value="molecular_analysis">Molecular / Phylogenetic Analysis</option>
                                <option value="robustness">Robustness & Sensitivity Check</option>
                                <option value="expert_review">Independent Expert Review</option>
                                <option value="evidence_synthesis">Evidence Synthesis & Claim Formulation</option>
                            </select>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label fw-semibold">Display Sequence Order</label>
                            <input type="number" name="display_order" class="form-control" value="<?= count($steps) + 1 ?>">
                        </div>
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-semibold">Scientific Goal</label>
                        <textarea name="scientific_goal" class="form-control" rows="2" required placeholder="What scientific milestone is achieved by this step?"></textarea>
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-semibold">Scientific Rationale</label>
                        <textarea name="rationale" class="form-control" rows="2" required placeholder="Why is this step necessary to answer the research question?"></textarea>
                    </div>
                    <div class="row g-3 mb-3">
                        <div class="col-md-6">
                            <div class="form-check mt-4">
                                <input class="form-check-input" type="checkbox" name="requires_capability" id="reqCap" value="1">
                                <label class="form-check-label" for="reqCap">Requires Registered Capability / Tool</label>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-check mt-4">
                                <input class="form-check-input" type="checkbox" name="requires_experiment" id="reqExp" value="1">
                                <label class="form-check-label" for="reqExp">Requires Experiment Run</label>
                            </div>
                        </div>
                    </div>
                    <div class="row g-3 mb-3">
                        <div class="col-md-6">
                            <label class="form-label fw-semibold">Expected Evidence</label>
                            <input type="text" name="expected_evidence" class="form-control" placeholder="e.g. Calibrated landmark coordinates table">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label fw-semibold">Completion Criteria</label>
                            <input type="text" name="completion_criteria" class="form-control" placeholder="e.g. All 120 specimens landmarked and validated">
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn btn-primary">Save Step</button>
                </div>
            </form>
        </div>
    </div>
</div>

<?php endif; ?>

<?php require_once __DIR__ . '/includes/footer.php'; ?>

