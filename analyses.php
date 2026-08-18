<?php

declare(strict_types=1);

require_once __DIR__ . '/includes/api.php';
require_once __DIR__ . '/includes/functions.php';


$projectId = 0;
$project = null;
$questions = [];
$hypotheses = [];
$datasets = [];
$plans = [];
$runs = [];
$resultsByRun = [];
$error = null;
$notice = null;

try {

    $projectId = getRequiredPositiveInt('project_id');

    $project = api_get(
        '/projects/' . $projectId
    );

    $questions = api_get(
        '/projects/' . $projectId . '/questions'
    );

    $hypotheses = api_get(
        '/projects/' . $projectId . '/hypotheses'
    );

    $datasets = api_get(
        '/projects/' . $projectId . '/datasets'
    );

    $plans = api_get(
        '/projects/' . $projectId . '/experiments'
    );

    $runs = api_get(
        '/projects/' . $projectId . '/experiment-runs'
    );

    $capabilities = api_get('/capabilities');
    if (!is_array($capabilities)) {
        $capabilities = [];
    }

    $allInvestigationSteps = [];
    if (is_array($questions)) {
        foreach ($questions as $q) {
            $qSteps = api_get('/questions/' . $q['id'] . '/investigation-steps');
            if (is_array($qSteps)) {
                foreach ($qSteps as $qs) {
                    $allInvestigationSteps[] = $qs;
                }
            }
        }
    }

    $postError = null;

    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        try {

        $action = filter_input(INPUT_POST, 'action') ?? '';

        $projectPlanIds = array_map(
            static fn (array $plan): int => (int)$plan['id'],
            $plans
        );

        if ($action === 'plan_experiment_ai') {
            $stepId = filter_input(INPUT_POST, 'investigation_step_id', FILTER_VALIDATE_INT);
            if (!$stepId || $stepId < 1) {
                throw new InvalidArgumentException('Please select a valid investigation step.');
            }
            $userGuidance = trim($_POST['user_guidance'] ?? '');
            api_post('/investigation-steps/' . $stepId . '/experiments/plan', [
                'user_guidance' => $userGuidance !== '' ? $userGuidance : null,
            ]);
            $noticeKey = 'exp_planned=1';

        } elseif ($action === 'approve_experiment') {
            $planId = filter_input(INPUT_POST, 'analysis_plan_id', FILTER_VALIDATE_INT);
            if (!$planId || $planId < 1) {
                throw new InvalidArgumentException('Invalid experiment plan ID.');
            }
            api_post('/experiments/' . $planId . '/approve', []);
            $noticeKey = 'exp_approved=1';

        } elseif ($action === 'override_parameters') {
            $planId = filter_input(INPUT_POST, 'analysis_plan_id', FILTER_VALIDATE_INT);
            if (!$planId || $planId < 1) {
                throw new InvalidArgumentException('Invalid experiment plan ID.');
            }
            $paramsRaw = trim($_POST['parameters'] ?? '');
            $justification = trim($_POST['justification'] ?? '');
            $params = json_decode($paramsRaw, true);
            if (json_last_error() !== JSON_ERROR_NONE) {
                throw new InvalidArgumentException('Invalid JSON for parameters: ' . json_last_error_msg());
            }
            api_put('/experiments/' . $planId . '/parameters', [
                'parameters' => $params,
                'justification' => $justification !== '' ? $justification : null,
            ]);
            $noticeKey = 'params_updated=1';

        } elseif ($action === 'create_plan') {
            $questionId = filter_input(INPUT_POST, 'question_id', FILTER_VALIDATE_INT);
            if (!$questionId || $questionId < 1) {
                throw new InvalidArgumentException('Please select a valid research question.');
            }
            $hypothesisId = filter_input(INPUT_POST, 'hypothesis_id', FILTER_VALIDATE_INT);
            $datasetVersionId = filter_input(INPUT_POST, 'dataset_version_id', FILTER_VALIDATE_INT);
            $method = trim($_POST['method'] ?? '');
            if ($method === '') {
                throw new InvalidArgumentException('Analysis method is required.');
            }
            $estimand = trim($_POST['estimand'] ?? '');
            $exploratory = !empty($_POST['exploratory']);

            $paramsRaw = trim($_POST['parameters'] ?? '');
            $params = null;
            if ($paramsRaw !== '') {
                $params = json_decode($paramsRaw, true);
                if (json_last_error() !== JSON_ERROR_NONE) {
                    throw new InvalidArgumentException('Invalid JSON for parameters: ' . json_last_error_msg());
                }
            }

            $assumpRaw = trim($_POST['assumptions'] ?? '');
            $assumptions = null;
            if ($assumpRaw !== '') {
                $assumptions = json_decode($assumpRaw, true);
                if (json_last_error() !== JSON_ERROR_NONE) {
                    throw new InvalidArgumentException('Invalid JSON for assumptions: ' . json_last_error_msg());
                }
            }

            $payload = [
                'hypothesis_id' => $hypothesisId && $hypothesisId > 0 ? $hypothesisId : null,
                'dataset_version_id' => $datasetVersionId && $datasetVersionId > 0 ? $datasetVersionId : null,
                'method' => $method,
                'estimand' => $estimand !== '' ? $estimand : null,
                'parameters' => $params,
                'assumptions' => $assumptions,
                'exploratory' => $exploratory,
            ];

            api_post('/questions/' . $questionId . '/experiments', $payload);
            $noticeKey = 'plan_created=1';

        } elseif ($action === 'create_run') {
            $planId = filter_input(
                INPUT_POST,
                'analysis_plan_id',
                FILTER_VALIDATE_INT
            );

            if (
                $planId === false ||
                $planId === null ||
                $planId < 1 ||
                !in_array($planId, $projectPlanIds, true)
            ) {
                throw new InvalidArgumentException(
                    'Invalid analysis plan.'
                );
            }

            api_post(
                '/experiments/' . $planId . '/runs',
                ['parameters' => null]
            );

            $noticeKey = 'run_created=1';

        } elseif ($action === 'create_run_custom') {
            $planId = filter_input(INPUT_POST, 'analysis_plan_id', FILTER_VALIDATE_INT);
            if ($planId === false || $planId === null || $planId < 1 || !in_array($planId, $projectPlanIds, true)) {
                throw new InvalidArgumentException('Invalid analysis plan.');
            }
            $customParamsRaw = trim($_POST['custom_parameters'] ?? '');
            $customParams = null;
            if ($customParamsRaw !== '') {
                $customParams = json_decode($customParamsRaw, true);
                if (json_last_error() !== JSON_ERROR_NONE) {
                    throw new InvalidArgumentException('Invalid JSON for parameters: ' . json_last_error_msg());
                }
            }
            $execMetaRaw = trim($_POST['execution_metadata'] ?? '');
            $execMeta = null;
            if ($execMetaRaw !== '') {
                $execMeta = json_decode($execMetaRaw, true);
            }
            api_post('/experiments/' . $planId . '/runs', [
                'parameters' => $customParams,
                'execution_metadata' => $execMeta
            ]);
            $noticeKey = 'run_created=1';
        } elseif ($action === 'start_run') {
            $runId = filter_input(INPUT_POST, 'analysis_run_id', FILTER_VALIDATE_INT);
            if ($runId) {
                api_post('/experiment-runs/' . $runId . '/start', ['parameters' => null]);
                $noticeKey = 'run_started=1';
            }
        } elseif ($action === 'complete_run') {
            $runId = filter_input(INPUT_POST, 'analysis_run_id', FILTER_VALIDATE_INT);
            if ($runId) {
                api_post('/experiment-runs/' . $runId . '/complete', ['execution_metadata' => null]);
                $noticeKey = 'run_completed=1';
            }
        } elseif ($action === 'fail_run') {
            $runId = filter_input(INPUT_POST, 'analysis_run_id', FILTER_VALIDATE_INT);
            $errType = trim($_POST['error_type'] ?? 'ExecutionError');
            $errMsg = trim($_POST['error_message'] ?? 'Execution failed');
            if ($runId) {
                api_post('/experiment-runs/' . $runId . '/fail', [
                    'error_type' => $errType,
                    'error_message' => $errMsg
                ]);
                $noticeKey = 'run_failed=1';
            }
        } elseif ($action === 'execute_run') {
            $runId = filter_input(
                INPUT_POST,
                'analysis_run_id',
                FILTER_VALIDATE_INT
            );

            $projectRunIds = array_map(
                static fn (array $run): int => (int)$run['id'],
                $runs
            );

            if (
                $runId === false ||
                $runId === null ||
                $runId < 1 ||
                !in_array($runId, $projectRunIds, true)
            ) {
                throw new InvalidArgumentException(
                    'Invalid analysis run.'
                );
            }

            api_post_empty(
                '/experiment-runs/' . $runId . '/execute'
            );

            $noticeKey = 'run_executed=1';

        } else {
            throw new InvalidArgumentException(
                'Invalid analysis action.'
            );
        }

            header(
                'Location: analyses.php?project_id=' .
                $projectId .
                '&' .
                $noticeKey
            );
            exit;
        } catch (Throwable $postEx) {
            $postError = $postEx->getMessage();
        }
    }

    if (filter_input(INPUT_GET, 'plan_created') === '1') {
        $notice = 'New Experiment created and linked successfully!';
    } elseif (filter_input(INPUT_GET, 'exp_planned') === '1') {
        $notice = 'Phase 10: Experiment successfully pre-specified via LLM Stage 4 reasoning!';
    } elseif (filter_input(INPUT_GET, 'exp_approved') === '1') {
        $notice = 'Experiment approved and frozen for computational execution.';
    } elseif (filter_input(INPUT_GET, 'params_updated') === '1') {
        $notice = 'Experiment runtime parameters updated successfully with researcher justification.';
    } elseif (filter_input(INPUT_GET, 'run_created') === '1') {
        $notice = (
            'Experiment run created in pending state. ' .
            'No scientific analysis has been executed yet.'
        );
    } elseif (filter_input(INPUT_GET, 'run_executed') === '1') {
        $notice = (
            'The registered executor completed and its ' .
            'Result record was persisted.'
        );
    }

    foreach ($runs as $run) {
        $runId = (int)$run['id'];
        $resultsByRun[$runId] = api_get(
            '/experiment-runs/' . $runId . '/results'
        );
    }


} catch (Throwable $e) {

    $error = $e->getMessage();
}


$activePage = 'analyses';


$questionsById = [];

foreach ($questions as $question) {
    $questionsById[(int)$question['id']] = $question;
}


$hypothesesById = [];

foreach ($hypotheses as $hypothesis) {
    $hypothesesById[(int)$hypothesis['id']] = $hypothesis;
}


$datasetsById = [];

foreach ($datasets as $dataset) {
    $datasetsById[(int)$dataset['id']] = $dataset;
}

$runsByPlan = [];

foreach ($runs as $run) {

    $analysisPlanId =
        (int)$run['analysis_plan_id'];

    $runsByPlan[$analysisPlanId][] =
        $run;
}

?>
<!doctype html>

<html lang="en">

<head>

    <meta charset="utf-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >

    <title>
        Experiments - Biodiversity AI Scientist
    </title>

    <link
        href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css"
        rel="stylesheet"
    >

    <link
        href="css/app.css"
    <link
        href="css/app.css"
        rel="stylesheet"
    >
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">

</head>


<body class="bg-light">

<?php require_once __DIR__ . '/includes/navbar.php'; ?>



<?php if ($error !== null): ?>

    <div class="container py-5">

        <div class="alert alert-danger">

            <h1 class="h5">
                Unable to load analyses
            </h1>

            <p class="mb-3">
                <?= h($error) ?>
            </p>

            <a
                href="projects.php"
                class="btn btn-outline-danger"
            >
                Back to projects
            </a>

        </div>

    </div>


<?php else: ?>


<div class="container-fluid">


    <div class="row border-bottom bg-white">

        <div class="col-12 px-4 py-3">

            <div class="d-flex
                        justify-content-between
                        align-items-start">

                <div>

                    <div class="text-muted small mb-1">

                        Research Project
                        #<?= (int)$project['id'] ?>

                    </div>

                    <h1 class="h4 mb-1">
                        <?= h($project['title']) ?>
                    </h1>
                    <?php if (!empty($project['objective'])): ?>
                        <div class="text-muted small mt-1">
                            <i class="bi bi-card-text text-primary me-1"></i><?= h($project['objective']) ?>
                        </div>
                    <?php endif; ?>
                </div>
                <div>
                    <a
                        href="project.php?project_id=<?= $projectId ?>"
                        class="btn btn-sm btn-outline-secondary"
                    >
                        Project overview
                    </a>


                </div>

            </div>

        </div>

    </div>


    <div class="row">


        <?php require __DIR__ . '/includes/menu.php'; ?>


        <main class="col-md-9 col-lg-10 p-4">


            <div class="d-flex
                        justify-content-between
                        align-items-start
                        mb-4">

                <div>

                    <h2 class="h3 mb-1">
                        Experiments
                    </h2>

                    <p class="text-muted mb-0">
                        Pre-specified Experiments and their computational Experiment Runs.
                    </p>

                </div>

                <div class="d-flex align-items-center gap-2">
                    <a href="help/analyses.php?project_id=<?= $projectId ?>" class="btn btn-outline-secondary btn-sm">
                        📖 Guide &amp; Help
                    </a>
                    <span class="badge bg-light text-dark border fs-6">
                        <?= count($plans) ?> experiment<?= count($plans) === 1 ? '' : 's' ?>
                    </span>
                    <button type="button" class="btn btn-outline-primary btn-sm fw-semibold shadow-sm" data-bs-toggle="modal" data-bs-target="#planExperimentAiModal">
                        <i class="bi bi-magic me-1"></i> ⚡ Plan Experiment with AI
                    </button>
                    <button type="button" class="btn btn-primary btn-sm fw-semibold shadow-sm" data-bs-toggle="modal" data-bs-target="#createPlanModal">
                        + Create Experiment
                    </button>
                </div>

            </div>


            <div class="alert alert-info">
                An <strong>Experiment</strong> defines a specific computational or empirical procedure used to generate evidence for a research question. An <strong>Experiment Run</strong> records one actual execution of an Experiment, including its inputs, runtime parameters, lifecycle status, outputs, and failure diagnostics.
            </div>

            <?php if (!empty($postError)): ?>
                <div class="alert alert-warning alert-dismissible fade show mb-4" role="alert">
                    <strong>Notice:</strong> <?= h($postError) ?>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            <?php endif; ?>

            <?php if ($notice !== null): ?>
                <div class="alert alert-success alert-dismissible fade show mb-4" role="alert">
                    <?= h($notice) ?>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            <?php endif; ?>


            <?php if (count($plans) === 0): ?>


                <div class="card shadow-sm">

                    <div class="card-body text-center py-5">

                        <h3 class="h5">
                            No experiments registered
                        </h3>

                        <p class="text-muted mb-0">
                            No pre-specified experiment has yet been registered for this project.
                        </p>

                    </div>

                </div>


            <?php else: ?>


                <?php foreach ($plans as $plan): ?>


                    <?php

                    $questionId =
                        (int)$plan['question_id'];

                    $hypothesisId =
                        $plan['hypothesis_id'] !== null
                            ? (int)$plan['hypothesis_id']
                            : null;

                    $datasetId =
                        $plan['dataset_version_id'] !== null
                            ? (int)$plan['dataset_version_id']
                            : null;

                    $question =
                        $questionsById[$questionId] ?? null;

                    $hypothesis =
                        $hypothesisId !== null
                            ? ($hypothesesById[$hypothesisId] ?? null)
                            : null;

                    $dataset =
                        $datasetId !== null
                            ? ($datasetsById[$datasetId] ?? null)
                            : null;

                    ?>


                    <?php 
                    $expAssumptions = $plan['assumptions'] ?? [];
                    $workingTitle = $expAssumptions['working_title'] ?? null;
                    $stepId = $expAssumptions['investigation_step_id'] ?? null;
                    $paramJusts = $expAssumptions['parameter_justifications'] ?? [];
                    ?>
                    <div class="card shadow-sm mb-4" id="plan-<?= (int)$plan['id'] ?>">


                        <div class="card-header bg-white">

                            <div class="d-flex justify-content-between align-items-center">

                                <div>
                                    <strong>
                                        Experiment #<?= (int)$plan['id'] ?>
                                    </strong>
                                    <?php if ($workingTitle): ?>
                                        <span class="ms-2 fw-semibold text-primary">— <?= h($workingTitle) ?></span>
                                    <?php endif; ?>
                                    <?php if ($stepId): ?>
                                        <a href="investigation_plan.php?project_id=<?= $projectId ?>#step-<?= (int)$stepId ?>" class="badge bg-secondary-subtle text-secondary border text-decoration-none ms-2">
                                            <i class="bi bi-diagram-3 me-1"></i>Step #<?= (int)$stepId ?>
                                        </a>
                                    <?php endif; ?>
                                </div>


                                <div class="d-flex align-items-center gap-2">

                                    <?php if ($plan['exploratory']): ?>
                                        <span class="badge bg-warning text-dark">
                                            Exploratory
                                        </span>
                                    <?php else: ?>
                                        <span class="badge bg-primary">
                                            Confirmatory
                                        </span>
                                    <?php endif; ?>

                                    <span class="badge <?= statusBadge($plan['status']) ?>">
                                        <?= h(strtoupper($plan['status'])) ?>
                                    </span>

                                    <?php if ($plan['status'] === 'draft' || $plan['status'] === 'proposed'): ?>
                                        <form method="post" class="d-inline mb-0">
                                            <input type="hidden" name="action" value="approve_experiment">
                                            <input type="hidden" name="analysis_plan_id" value="<?= (int)$plan['id'] ?>">
                                            <button type="submit" class="btn btn-sm btn-success py-0 px-2 fw-semibold" title="Approve & Freeze Experiment specification for execution">
                                                <i class="bi bi-check2-circle me-1"></i>Approve
                                            </button>
                                        </form>
                                        <button type="button" class="btn btn-sm btn-outline-secondary py-0 px-2" data-bs-toggle="modal" data-bs-target="#overrideModal-<?= (int)$plan['id'] ?>" title="Override parameters">
                                            <i class="bi bi-sliders me-1"></i>Edit Parameters
                                        </button>
                                    <?php endif; ?>

                                </div>

                            </div>

                        </div>


                        <div class="card-body">


                            <div class="row g-4">


                                <div class="col-lg-7">


                                    <div class="mb-4">

                                        <div class="small
                                                    text-uppercase
                                                    text-muted
                                                    fw-semibold
                                                    mb-1">

                                            Method

                                        </div>

                                        <div class="fs-5 fw-semibold">

                                            <?= h($plan['method']) ?>

                                        </div>

                                    </div>


                                    <div class="mb-4">

                                        <div class="small
                                                    text-uppercase
                                                    text-muted
                                                    fw-semibold
                                                    mb-1">

                                            Research question

                                        </div>

                                        <?php if ($question !== null): ?>

                                            <div>
                                                Q<?= $questionId ?> —
                                                <?= h($question['question']) ?>
                                            </div>

                                        <?php else: ?>

                                            <span class="text-muted">
                                                Q<?= $questionId ?>
                                            </span>

                                        <?php endif; ?>

                                    </div>


                                    <div class="mb-4">

                                        <div class="small
                                                    text-uppercase
                                                    text-muted
                                                    fw-semibold
                                                    mb-1">

                                            Hypothesis

                                        </div>

                                        <?php if ($hypothesis !== null): ?>

                                            <div>
                                                H<?= $hypothesisId ?> —
                                                <?= h($hypothesis['statement']) ?>
                                            </div>

                                        <?php elseif ($hypothesisId !== null): ?>

                                            <span class="text-muted">
                                                H<?= $hypothesisId ?>
                                            </span>

                                        <?php else: ?>

                                            <span class="text-muted">
                                                No hypothesis linked
                                            </span>

                                        <?php endif; ?>

                                    </div>


                                    <div class="mb-4">

                                        <div class="small
                                                    text-uppercase
                                                    text-muted
                                                    fw-semibold
                                                    mb-1">

                                            Estimand

                                        </div>

                                        <?php if (!empty($plan['estimand'])): ?>

                                            <p class="mb-0">
                                                <?= nl2br(
                                                    h($plan['estimand'])
                                                ) ?>
                                            </p>

                                        <?php else: ?>

                                            <span class="text-muted">
                                                Not specified
                                            </span>

                                        <?php endif; ?>

                                    </div>


                                </div>


                                <div class="col-lg-5">


                                    <table class="table table-sm">

                                        <tbody>

                                        <tr>
                                            <th style="width: 42%;">
                                                Dataset
                                            </th>

                                            <td>

                                                <?php if ($dataset !== null): ?>

                                                    <?= h(
                                                        $dataset['version_key']
                                                    ) ?>

                                                <?php elseif ($datasetId !== null): ?>

                                                    Dataset #<?= $datasetId ?>

                                                <?php else: ?>

                                                    <span class="text-muted">
                                                        Not specified
                                                    </span>

                                                <?php endif; ?>

                                            </td>

                                        </tr>


                                        <tr>
                                            <th>
                                                Analysis type
                                            </th>

                                            <td>

                                                <?= $plan['exploratory']
                                                    ? 'Exploratory'
                                                    : 'Confirmatory' ?>

                                            </td>

                                        </tr>


                                        <tr>
                                            <th>
                                                Status
                                            </th>

                                            <td>
                                                <?= h($plan['status']) ?>
                                            </td>

                                        </tr>


                                        <tr>
                                            <th>
                                                Created
                                            </th>

                                            <td>

                                                <?php

                                                $created = new DateTime(
                                                    $plan['created_at']
                                                );

                                                echo h(
                                                    $created->format(
                                                        'Y-m-d H:i:s'
                                                    )
                                                );

                                                ?>

                                            </td>

                                        </tr>

                                        </tbody>

                                    </table>


                                </div>


                            </div>


                            <hr>


                            <div class="row g-4">


                                <?php if (!empty($expAssumptions['protocol_description']) || !empty($paramJusts) || !empty($expAssumptions['interpretation_criteria'])): ?>
                                    <div class="col-12">
                                        <div class="p-3 bg-light rounded border mb-3">
                                            <div class="fw-bold text-dark mb-2"><i class="bi bi-journal-text text-primary me-1"></i> Scientific Protocol & Experimental Design</div>
                                            <p class="text-secondary small mb-2"><?= nl2br(h($expAssumptions['protocol_description'] ?? 'N/A')) ?></p>
                                            
                                            <div class="row g-2 small text-muted mt-2 pt-2 border-top">
                                                <div class="col-md-6">
                                                    <strong>Control Strategy:</strong> <?= h($expAssumptions['control_strategy'] ?? 'Standard negative/positive controls') ?>
                                                </div>
                                                <div class="col-md-6">
                                                    <strong>Replication Strategy:</strong> <?= h($expAssumptions['replication_strategy'] ?? 'Standard run replication') ?>
                                                </div>
                                            </div>
                                        </div>

                                        <?php if (!empty($paramJusts)): ?>
                                            <div class="mb-3">
                                                <div class="small text-uppercase text-muted fw-semibold mb-2">
                                                    <i class="bi bi-sliders text-secondary me-1"></i> Pre-specified Parameters & Scientific Justifications
                                                </div>
                                                <div class="table-responsive">
                                                    <table class="table table-sm table-bordered bg-white small mb-0">
                                                        <thead class="table-light">
                                                            <tr>
                                                                <th style="width: 25%;">Parameter</th>
                                                                <th style="width: 20%;">Pre-specified Value</th>
                                                                <th>Scientific Justification</th>
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            <?php foreach ($paramJusts as $pj): ?>
                                                                <tr>
                                                                    <td><code><?= h((string)$pj['parameter_name']) ?></code></td>
                                                                    <td><strong><?= h(is_array($pj['value']) ? json_encode($pj['value']) : (string)$pj['value']) ?></strong></td>
                                                                    <td class="text-secondary"><?= h((string)$pj['scientific_justification']) ?></td>
                                                                </tr>
                                                            <?php endforeach; ?>
                                                        </tbody>
                                                    </table>
                                                </div>
                                            </div>
                                        <?php endif; ?>

                                        <?php if (!empty($expAssumptions['interpretation_criteria'])): ?>
                                            <div class="alert alert-primary-subtle border border-primary-subtle p-3 mb-3 small">
                                                <div class="fw-bold text-primary mb-1">
                                                    <i class="bi bi-compass text-primary me-1"></i> Result Interpretation Decision Rules (Phase 13 Protocol):
                                                </div>
                                                <div class="text-secondary"><?= nl2br(h($expAssumptions['interpretation_criteria'])) ?></div>
                                            </div>
                                        <?php endif; ?>

                                        <?php if (!empty($expAssumptions['known_limitations_and_confounders'])): ?>
                                            <div class="p-2 bg-light-subtle border rounded small text-muted mb-0">
                                                <strong class="text-warning-emphasis"><i class="bi bi-exclamation-triangle me-1"></i> Known Limitations & Confounders:</strong>
                                                <ul class="mb-0 ps-3 mt-1">
                                                    <?php foreach ($expAssumptions['known_limitations_and_confounders'] as $lim): ?>
                                                        <li><?= h((string)$lim) ?></li>
                                                    <?php endforeach; ?>
                                                </ul>
                                            </div>
                                        <?php endif; ?>
                                    </div>
                                <?php else: ?>
                                    <div class="col-lg-6">
                                        <div class="small text-uppercase text-muted fw-semibold mb-2">Assumptions</div>
                                        <?php if ($plan['assumptions'] === null): ?>
                                            <span class="text-muted">No assumptions registered.</span>
                                        <?php else: ?>
                                            <pre class="bg-light border rounded p-3 mb-0"><code><?= h(json_encode($plan['assumptions'], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES)) ?></code></pre>
                                        <?php endif; ?>
                                    </div>
                                    <div class="col-lg-6">
                                        <div class="small text-uppercase text-muted fw-semibold mb-2">Parameters</div>
                                        <?php if ($plan['parameters'] === null): ?>
                                            <span class="text-muted">No parameters registered.</span>
                                        <?php else: ?>
                                            <pre class="bg-light border rounded p-3 mb-0"><code><?= h(json_encode($plan['parameters'], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES)) ?></code></pre>
                                        <?php endif; ?>
                                    </div>
                                <?php endif; ?>

                                <!-- Override Parameters Modal for Plan -->
                                <div class="modal fade" id="overrideModal-<?= (int)$plan['id'] ?>" tabindex="-1" aria-hidden="true">
                                    <div class="modal-dialog">
                                        <div class="modal-content">
                                            <form method="post" action="analyses.php?project_id=<?= $projectId ?>">
                                                <input type="hidden" name="action" value="override_parameters">
                                                <input type="hidden" name="analysis_plan_id" value="<?= (int)$plan['id'] ?>">
                                                <div class="modal-header">
                                                    <h5 class="modal-title">Edit / Override Parameters for Experiment #<?= (int)$plan['id'] ?></h5>
                                                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                                                </div>
                                                <div class="modal-body">
                                                    <div class="mb-3">
                                                        <label class="form-label fw-semibold">Parameters (JSON)</label>
                                                        <textarea name="parameters" class="form-control font-monospace" rows="6" required><?= h(json_encode($plan['parameters'] ?? new stdClass(), JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES)) ?></textarea>
                                                    </div>
                                                    <div class="mb-3">
                                                        <label class="form-label fw-semibold">Researcher Justification</label>
                                                        <textarea name="justification" class="form-control" rows="2" placeholder="State scientific rationale for manual override..." required><?= h($expAssumptions['researcher_override_justification'] ?? '') ?></textarea>
                                                    </div>
                                                </div>
                                                <div class="modal-footer">
                                                    <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
                                                    <button type="submit" class="btn btn-primary">Save Parameter Overrides</button>
                                                </div>
                                            </form>
                                        </div>
                                    </div>
                                </div>

<?php

$planId = (int)$plan['id'];

$planRuns =
    $runsByPlan[$planId] ?? [];

?>

<hr class="my-4">


<div class="d-flex
            justify-content-between
            align-items-center
            mb-3">

    <div>

        <div class="small
                    text-uppercase
                    text-muted
                    fw-semibold">

            Experiment Runs

        </div>

    </div>

    <div class="d-flex align-items-center gap-2">

        <span class="badge bg-light text-dark border">
            <?= count($planRuns) ?>
        </span>

        <form method="post" class="mb-0">
            <input
                type="hidden"
                name="action"
                value="create_run"
            >
            <input
                type="hidden"
                name="analysis_plan_id"
                value="<?= $planId ?>"
            >
            <button
                type="submit"
                class="btn btn-sm btn-outline-primary"
            >
                Create Experiment Run
            </button>
        </form>

    </div>

</div>


<?php if (count($planRuns) === 0): ?>

    <p class="text-muted mb-0">

        No execution run has been created for this plan.

    </p>

<?php else: ?>


    <?php foreach ($planRuns as $run): ?>

        <?php

        $runId = (int)$run['id'];
        $runResults = $resultsByRun[$runId] ?? [];

        ?>

        <div class="border rounded p-3 mb-3 bg-light">


            <div class="d-flex
                        justify-content-between
                        align-items-start
                        mb-3">

                <div>

                    <strong>
                        Experiment Run #<?= (int)$run['id'] ?>
                    </strong>

                    <?php if (!empty($run['tool_name'])): ?>

                        <span class="text-muted ms-2">

                            <?= h($run['tool_name']) ?>

                            <?php if (!empty($run['tool_version'])): ?>

                                <?= h($run['tool_version']) ?>

                            <?php endif; ?>

                        </span>

                    <?php endif; ?>

                </div>


                <div class="d-flex align-items-center gap-2">

                    <?php if ($run['status'] === 'pending'): ?>
                        <?php 
                        $isAutomated = in_array($plan['method'] ?? '', ['dataset_registration_summary', 'Workflow integrity validation'], true);
                        if ($isAutomated): 
                        ?>
                            <form method="post" class="mb-0">
                                <input type="hidden" name="action" value="execute_run">
                                <input type="hidden" name="analysis_run_id" value="<?= $runId ?>">
                                <button type="submit" class="btn btn-sm btn-primary">
                                    ▶ Execute Analysis
                                </button>
                            </form>
                        <?php else: ?>
                            <form method="post" class="mb-0 d-inline">
                                <input type="hidden" name="action" value="start_run">
                                <input type="hidden" name="analysis_run_id" value="<?= $runId ?>">
                                <button type="submit" class="btn btn-sm btn-outline-primary" title="Transition state to running (e.g. while external PyTorch job runs)">
                                    ▶ Start Run
                                </button>
                            </form>
                        <?php endif; ?>
                    <?php elseif ($run['status'] === 'running'): ?>
                        <form method="post" class="mb-0 d-inline">
                            <input type="hidden" name="action" value="complete_run">
                            <input type="hidden" name="analysis_run_id" value="<?= $runId ?>">
                            <button type="submit" class="btn btn-sm btn-success">
                                ✔ Mark Completed
                            </button>
                        </form>
                        <button type="button" class="btn btn-sm btn-outline-danger" data-bs-toggle="modal" data-bs-target="#failRunModal<?= $runId ?>">
                            ✖ Record Failure
                        </button>

                        <!-- Fail Modal for Run -->
                        <div class="modal fade" id="failRunModal<?= $runId ?>" tabindex="-1" aria-hidden="true">
                            <div class="modal-dialog">
                                <div class="modal-content">
                                    <form method="post" action="analyses.php?project_id=<?= $projectId ?>">
                                        <input type="hidden" name="action" value="fail_run">
                                        <input type="hidden" name="analysis_run_id" value="<?= $runId ?>">
                                        <div class="modal-header bg-danger text-white">
                                            <h5 class="modal-title">Record Execution Failure</h5>
                                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                                        </div>
                                        <div class="modal-body">
                                            <p class="small text-muted mb-3">
                                                Failed runs are preserved permanently in the database for scientific integrity.
                                            </p>
                                            <div class="mb-3">
                                                <label class="form-label fw-semibold">Error Type</label>
                                                <input type="text" name="error_type" class="form-control" value="OutOfMemoryError" required>
                                            </div>
                                            <div class="mb-3">
                                                <label class="form-label fw-semibold">Error Message / Reason</label>
                                                <textarea name="error_message" class="form-control" rows="3" required placeholder="e.g. CUDA out of memory during epoch 12..."></textarea>
                                            </div>
                                        </div>
                                        <div class="modal-footer">
                                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                            <button type="submit" class="btn btn-danger">Preserve Failure State</button>
                                        </div>
                                    </form>
                                </div>
                            </div>
                        </div>
                    <?php endif; ?>

                    <span class="badge <?= statusBadge(
                        $run['status']
                    ) ?>">

                        <?= h($run['status']) ?>

                    </span>

                </div>

            </div>


            <div class="row g-3">


                <div class="col-md-3">

                    <div class="small text-muted">
                        Dataset Version
                    </div>

                    <div>

                        <?php
                        if ($run['dataset_version_id'] !== null) {

                            $runDatasetId =
                                (int)$run['dataset_version_id'];

                            $runDataset =
                                $datasetsById[
                                    $runDatasetId
                                ] ?? null;

                            if ($runDataset !== null) {

                                echo h(
                                    $runDataset[
                                        'version_key'
                                    ]
                                );

                            } else {

                                echo 'Dataset #' .
                                     $runDatasetId;
                            }

                        } else {

                            echo '<span class="text-muted">None</span>';
                        }
                        ?>

                    </div>

                </div>


                <div class="col-md-3">

                    <div class="small text-muted">
                        Created
                    </div>

                    <div>

                        <?php

                        $runCreated =
                            new DateTime(
                                $run['created_at']
                            );

                        echo h(
                            $runCreated->format(
                                'Y-m-d H:i:s'
                            )
                        );

                        ?>

                    </div>

                </div>


                <div class="col-md-3">

                    <div class="small text-muted">
                        Started
                    </div>

                    <div>

                        <?php if (($run['started_at'] ?? null) !== null): ?>

                            <?php

                            $runStarted =
                                new DateTime(
                                    $run['started_at']
                                );

                            echo h(
                                $runStarted->format(
                                    'Y-m-d H:i:s'
                                )
                            );

                            ?>

                        <?php else: ?>

                            <span class="text-muted">
                                —
                            </span>

                        <?php endif; ?>

                    </div>

                </div>


                <div class="col-md-3">

                    <div class="small text-muted">
                        Finished
                    </div>

                    <div>

                        <?php if ($run['completed_at'] !== null): ?>

                            <?php

                            $runCompleted =
                                new DateTime(
                                    $run['completed_at']
                                );

                            echo h(
                                $runCompleted->format(
                                    'Y-m-d H:i:s'
                                )
                            );

                            ?>

                        <?php else: ?>

                            <span class="text-muted">
                                —
                            </span>

                        <?php endif; ?>

                    </div>

                </div>


            </div>


            <!-- Phase 2 Parameters & Execution Metadata -->
            <div class="row g-3 mt-1">
                <?php if (!empty($run['parameters'])): ?>
                    <div class="col-md-6">
                        <div class="small text-muted fw-semibold mb-1">Actual Parameters (Experiment Run)</div>
                        <pre class="bg-white border rounded p-2 mb-0 small" style="max-height: 120px; overflow-y: auto;"><code><?= h(json_encode($run['parameters'], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES)) ?></code></pre>
                    </div>
                <?php endif; ?>
                <?php if (!empty($run['execution_metadata'])): ?>
                    <div class="col-md-6">
                        <div class="small text-muted fw-semibold mb-1">Execution Metadata</div>
                        <pre class="bg-white border rounded p-2 mb-0 small" style="max-height: 120px; overflow-y: auto;"><code><?= h(json_encode($run['execution_metadata'], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES)) ?></code></pre>
                    </div>
                <?php endif; ?>
            </div>

            <?php if (!empty($run['error_message']) || !empty($run['error_type'])): ?>
                <div class="alert alert-danger mt-3 mb-0 p-3">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <span class="badge bg-danger"><?= h($run['error_type'] ?? 'ExecutionError') ?></span>
                        <small class="text-muted">Preserved Failure State</small>
                    </div>
                    <div class="fw-semibold text-danger mb-1"><?= h($run['error_message']) ?></div>
                    <?php if (!empty($run['error_details'])): ?>
                        <div class="mt-2 small">
                            <span class="text-muted fw-semibold">Error Diagnostics / Stack:</span>
                            <pre class="bg-dark text-light p-2 rounded mt-1 mb-0 font-monospace small" style="font-size: 11px; max-height: 150px; overflow-y: auto;"><code><?= h(is_array($run['error_details']) ? json_encode($run['error_details'], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES) : (string)$run['error_details']) ?></code></pre>
                        </div>
                    <?php endif; ?>
                </div>
            <?php endif; ?>


            <?php if (count($runResults) > 0): ?>

                <div class="mt-3">

                    <div class="small
                                text-uppercase
                                text-muted
                                fw-semibold
                                mb-2">
                        Results
                    </div>

                    <?php foreach ($runResults as $result): ?>

                        <div class="card bg-white mb-2">
                            <div class="card-body py-3">
                                <div class="fw-semibold mb-1">
                                    <?= h($result['result_type']) ?>
                                </div>

                                <?php if (!empty($result['summary'])): ?>
                                    <p class="mb-2">
                                        <?= h($result['summary']) ?>
                                    </p>
                                <?php endif; ?>

                                <?php if ($result['payload'] !== null): ?>
                                    <pre class="bg-light border rounded p-2 mb-0"><code><?= h(
                                        json_encode(
                                            $result['payload'],
                                            JSON_PRETTY_PRINT |
                                            JSON_UNESCAPED_SLASHES
                                        )
                                    ) ?></code></pre>
                                <?php endif; ?>
                            </div>
                        </div>

                    <?php endforeach; ?>

                </div>

            <?php endif; ?>


        </div>


    <?php endforeach; ?>


<?php endif; ?>


                            </div>


                        </div>

                    </div>


                <?php endforeach; ?>


            <?php endif; ?>


        </main>

    </div>

</div>


<?php endif; ?>


<script
    src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js">
</script>



<!-- Create Analysis Plan Modal -->
<div class="modal fade" id="createPlanModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <form method="post" action="analyses.php?project_id=<?= $projectId ?>">
                <input type="hidden" name="action" value="create_plan">
                <input type="hidden" name="project_id" value="<?= $projectId ?>">

                <div class="modal-header bg-primary text-white">
                    <h5 class="modal-title">Create Pre-specified Experiment</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <p class="small text-muted mb-3">
                        An Experiment defines a specific computational or empirical procedure used to generate evidence for a research question.
                    </p>

                    <div class="row g-3">
                        <div class="col-md-6">
                            <label class="form-label fw-semibold">Research Question <span class="text-danger">*</span></label>
                            <select name="question_id" class="form-select" required>
                                <option value="">-- Select Question --</option>
                                <?php foreach ($questions as $q): ?>
                                    <option value="<?= (int)$q['id'] ?>">Q<?= (int)$q['id'] ?>: <?= h(mb_strimwidth($q['question'], 0, 70, '...')) ?></option>
                                <?php endforeach; ?>
                            </select>
                        </div>

                        <div class="col-md-6">
                            <label class="form-label fw-semibold">Dataset Version</label>
                            <select name="dataset_version_id" class="form-select">
                                <option value="">-- No Dataset / Unspecified --</option>
                                <?php foreach ($datasets as $ds): ?>
                                    <option value="<?= (int)$ds['id'] ?>"><?= h($ds['version_key']) ?> (<?= h($ds['source_system']) ?>, <?= (int)($ds['member_count'] ?? 0) ?> items)</option>
                                <?php endforeach; ?>
                            </select>
                        </div>

                        <div class="col-md-6">
                            <label class="form-label fw-semibold">Candidate Hypothesis (Optional)</label>
                            <select name="hypothesis_id" class="form-select">
                                <option value="">-- No Hypothesis --</option>
                                <?php foreach ($hypotheses as $h): ?>
                                    <option value="<?= (int)$h['id'] ?>">H<?= (int)$h['id'] ?>: <?= h(mb_strimwidth($h['statement'], 0, 70, '...')) ?></option>
                                <?php endforeach; ?>
                            </select>
                        </div>

                        <div class="col-md-6">
                            <label class="form-label fw-semibold">Analysis Type</label>
                            <div class="form-check mt-2">
                                <input class="form-check-input" type="checkbox" name="exploratory" value="1" id="chk_exploratory">
                                <label class="form-check-label" for="chk_exploratory">
                                    Exploratory Analysis (vs Confirmatory)
                                </label>
                            </div>
                        </div>

                        <div class="col-12">
                            <label class="form-label fw-semibold">Registered Capability (Auto-fill Template)</label>
                            <select id="capability_preset_select" class="form-select border-primary" onchange="applyCapabilityPreset(this)">
                                <option value="">-- Choose a registered capability to pre-fill method &amp; parameters --</option>
                                <?php foreach ($capabilities as $capItem): ?>
                                    <option value="<?= h($capItem['capability_key']) ?>" 
                                            data-name="<?= h($capItem['display_name']) ?>" 
                                            data-purpose="<?= h($capItem['scientific_purpose']) ?>" 
                                            data-params="<?= h(json_encode($capItem['default_parameters'] ?? [], JSON_UNESCAPED_SLASHES)) ?>">
                                        ⚡ <?= h($capItem['display_name']) ?> (<?= h($capItem['reproducibility_level']) ?>)
                                    </option>
                                <?php endforeach; ?>
                            </select>
                        </div>

                        <div class="col-12">
                            <label class="form-label fw-semibold">Analytical Method <span class="text-danger">*</span></label>
                            <input type="text" id="input_plan_method" name="method" class="form-control" placeholder="e.g. DINOv3 feature extraction &amp; UMAP/HDBSCAN clustering" required>
                        </div>

                        <div class="col-12">
                            <label class="form-label fw-semibold">Estimand</label>
                            <input type="text" name="estimand" class="form-control" placeholder="e.g. Morphological cluster separability and classification accuracy">
                        </div>

                        <div class="col-md-6">
                            <label class="form-label fw-semibold">Proposed Parameters (JSON)</label>
                            <textarea name="parameters" class="form-control font-monospace small" rows="3" placeholder='{"model": "dinov3_vit_base", "batch_size": 32, "min_cluster_size": 5}'></textarea>
                        </div>

                        <div class="col-md-6">
                            <label class="form-label fw-semibold">Assumptions (JSON)</label>
                            <textarea name="assumptions" class="form-control font-monospace small" rows="3" placeholder='{"domain": "studio_only", "min_images_per_species": 15}'></textarea>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn btn-primary">Save Experiment</button>
                </div>
            </form>
        </div>
    </div>
<!-- Modal: Plan Experiment with AI (LLM Stage 4) -->
<div class="modal fade" id="planExperimentAiModal" tabindex="-1" aria-labelledby="planExperimentAiModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <form method="post" action="analyses.php?project_id=<?= $projectId ?>">
                <input type="hidden" name="action" value="plan_experiment_ai">
                <div class="modal-header bg-primary text-white">
                    <h5 class="modal-title" id="planExperimentAiModalLabel">
                        <i class="bi bi-magic me-2"></i>LLM Stage 4: Plan Experiment with AI
                    </h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div class="alert alert-info small mb-3">
                        Select an <strong>Investigation Step</strong> to synthesize. The LLM Gateway will assemble full grounded context (Phase 7), bind candidate capability input schemas (Phase 9), pre-specify parameter justifications, and formulate strict interpretation criteria (Phase 13).
                    </div>

                    <div class="mb-3">
                        <label class="form-label fw-semibold">Target Investigation Step <span class="text-danger">*</span></label>
                        <select name="investigation_step_id" class="form-select" required>
                            <option value="">-- Choose an Investigation Step --</option>
                            <?php foreach ($allInvestigationSteps as $st): ?>
                                <option value="<?= (int)$st['id'] ?>">
                                    Step #<?= (int)$st['id'] ?>: <?= h($st['title']) ?> (Goal: <?= h(mb_strimwidth($st['scientific_goal'], 0, 60, '...')) ?>)
                                </option>
                            <?php endforeach; ?>
                        </select>
                    </div>

                    <div class="mb-3">
                        <label class="form-label fw-semibold">Researcher Guidance / Protocol Constraints (Optional)</label>
                        <textarea name="user_guidance" class="form-control" rows="3" placeholder="e.g. Enforce 999 permutations, use cosine distance, adjust for specimen image source confounders..."></textarea>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn btn-primary">
                        <i class="bi bi-stars me-1"></i> Plan Experiment with AI
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>

<script>
function applyCapabilityPreset(selectElem) {
    const selectedOption = selectElem.options[selectElem.selectedIndex];
    if (!selectedOption || !selectedOption.value) return;

    const name = selectedOption.getAttribute('data-name');
    const purpose = selectedOption.getAttribute('data-purpose');
    const rawParams = selectedOption.getAttribute('data-params');

    const methodInput = document.getElementById('input_plan_method');
    if (methodInput && name) {
        methodInput.value = name;
    }

    const estimandInput = document.querySelector('input[name="estimand"]');
    if (estimandInput && purpose) {
        estimandInput.value = purpose;
    }

    const paramsInput = document.querySelector('textarea[name="parameters"]');
    if (paramsInput && rawParams) {
        try {
            const parsed = JSON.parse(rawParams);
            paramsInput.value = JSON.stringify(parsed, null, 2);
        } catch (e) {
            paramsInput.value = rawParams;
        }
    }
}
</script>
</body>
</html>
