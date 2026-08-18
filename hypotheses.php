<?php

declare(strict_types=1);

require_once __DIR__ . '/includes/api.php';
require_once __DIR__ . '/includes/functions.php';


/*
 * ------------------------------------------------------------
 * Load project, questions, hypotheses and predictions
 * ------------------------------------------------------------
 */

$projectId = 0;
$project = null;
$questions = [];
$hypotheses = [];
$predictionsByHypothesis = [];
$error = null;

$showArchived = !empty($_GET['show_archived']);
$showArch = $showArchived ? '&show_archived=1' : '';
$notice = null;

try {
    $projectId = getRequiredPositiveInt('project_id');

    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        $action = trim($_POST['action'] ?? '');
        $hId = filter_input(INPUT_POST, 'hypothesis_id', FILTER_VALIDATE_INT);

        if ($action === 'archive_hypothesis' && $hId) {
            api_patch('/hypotheses/' . $hId, ['status' => 'archived']);
            header('Location: hypotheses.php?project_id=' . $projectId . '&archived=1' . $showArch);
            exit;
        } elseif ($action === 'unarchive_hypothesis' && $hId) {
            api_patch('/hypotheses/' . $hId, ['status' => 'proposed']);
            header('Location: hypotheses.php?project_id=' . $projectId . '&unarchived=1' . $showArch);
            exit;
        } elseif ($action === 'set_status' && $hId) {
            $newStatus = trim($_POST['status'] ?? 'proposed');
            api_patch('/hypotheses/' . $hId, ['status' => $newStatus]);
            header('Location: hypotheses.php?project_id=' . $projectId . '&updated=1' . $showArch);
            exit;
        } elseif ($action === 'delete_hypothesis' && $hId) {
            api_delete('/hypotheses/' . $hId);
            header('Location: hypotheses.php?project_id=' . $projectId . '&deleted=1' . $showArch);
            exit;
        }
    }

    if (isset($_GET['archived'])) {
        $notice = 'Hypothesis archived / hidden.';
    } elseif (isset($_GET['unarchived'])) {
        $notice = 'Hypothesis unarchived (restored to proposed).';
    } elseif (isset($_GET['updated'])) {
        $notice = 'Hypothesis status updated.';
    } elseif (isset($_GET['deleted'])) {
        $notice = 'Hypothesis deleted permanently.';
    }

    $project = api_get('/projects/' . $projectId);
    $questions = api_get('/projects/' . $projectId . '/questions');
    $rawHypotheses = api_get('/projects/' . $projectId . '/hypotheses');

    $hypotheses = [];
    foreach ($rawHypotheses as $h) {
        if (!$showArchived && ($h['status'] ?? 'proposed') === 'archived') {
            continue;
        }
        $hypotheses[] = $h;
    }

    foreach ($hypotheses as $hypothesis) {
        $hypothesisId = (int)$hypothesis['id'];
        $predictionsByHypothesis[$hypothesisId] = api_get(
            '/hypotheses/' . $hypothesisId . '/predictions'
        );
    }

} catch (Throwable $e) {
    $error = $e->getMessage();
}


/*
 * ------------------------------------------------------------
 * Current workspace menu entry
 * ------------------------------------------------------------
 */

$activePage = 'hypotheses';


/*
 * ------------------------------------------------------------
 * Index questions by ID
 * ------------------------------------------------------------
 */

$questionsById = [];

foreach ($questions as $question) {

    $questionId = (int)$question['id'];

    $questionsById[$questionId] = $question;
}


/*
 * ------------------------------------------------------------
 * Group hypotheses by research question
 * ------------------------------------------------------------
 */

$hypothesesByQuestion = [];

foreach ($hypotheses as $hypothesis) {

    $questionId = (int)$hypothesis['question_id'];

    $hypothesesByQuestion[$questionId][] = $hypothesis;
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
        Hypotheses - Biodiversity AI Scientist
    </title>

    <link
        href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css"
        rel="stylesheet"
    >

    <link
        href="/ai-scientist/css/app.css"
        rel="stylesheet"
    >
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">

</head>


<body class="bg-light">


<!-- ============================================================
     Main navbar
     ============================================================ -->

<?php require_once __DIR__ . '/includes/navbar.php'; ?>



<?php if ($error !== null): ?>


    <!-- ========================================================
         Error state
         ======================================================== -->

    <div class="container py-5">

        <div class="alert alert-danger">

            <h1 class="h5">
                Unable to load hypotheses
            </h1>

            <p class="mb-3">
                <?= h($error) ?>
            </p>

            <a
                href="/ai-scientist/projects.php"
                class="btn btn-outline-danger"
            >
                Back to projects
            </a>

        </div>

    </div>


<?php else: ?>


    <div class="container-fluid">


        <!-- ====================================================
             Project header
             ==================================================== -->

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


            <!-- =================================================
                 Shared workspace navigation
                 ================================================= -->

            <?php require __DIR__ . '/includes/menu.php'; ?>


            <!-- =================================================
                 Main content
                 ================================================= -->

            <main class="col-md-9 col-lg-10 p-4">
                <?php if ($notice !== null): ?>
                    <div class="alert alert-success alert-dismissible fade show mb-4" role="alert">
                        <?= h($notice) ?>
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                <?php endif; ?>


                <div class="d-flex
                            justify-content-between
                            align-items-start
                            mb-4">

                    <div>

                        <h2 class="h3 mb-1">
                            Hypotheses
                        </h2>

                        <p class="text-muted mb-0">

                            Explicit scientific hypotheses
                            and their testable predictions.

                        </p>

                    </div>


                    <div class="d-flex align-items-center gap-2">
                        <a href="hypotheses.php?project_id=<?= $projectId ?><?= $showArchived ? '' : '&show_archived=1' ?>" class="btn btn-sm <?= $showArchived ? 'btn-secondary' : 'btn-outline-secondary' ?>">
                            <?= $showArchived ? 'Hide Archived' : 'Show Archived' ?>
                        </a>
                        <span class="badge bg-light text-dark border fs-6">
                            <?= count($hypotheses) ?> hypothesis<?= count($hypotheses) === 1 ? '' : 'es' ?>
                        </span>
                    </div>

                </div>


                <?php if (count($hypotheses) === 0): ?>


                    <!-- =========================================
                         Empty state
                         ========================================= -->

                    <div class="card shadow-sm">

                        <div class="card-body text-center py-5">

                            <h3 class="h5">
                                No hypotheses
                            </h3>

                            <p class="text-muted mb-0">

                                No hypotheses have yet been
                                registered for this project.

                            </p>

                        </div>

                    </div>


                <?php else: ?>


                    <!-- =========================================
                         Hypotheses grouped by question
                         ========================================= -->

                    <?php foreach ($questions as $question): ?>

                        <?php

                        $questionId = (int)$question['id'];

                        $questionHypotheses =
                            $hypothesesByQuestion[$questionId] ?? [];

                        if (count($questionHypotheses) === 0) {
                            continue;
                        }

                        ?>


                        <section class="mb-5">


                            <!-- Research question -->

                            <div class="mb-3">

                                <div class="small
                                            text-uppercase
                                            text-muted
                                            fw-semibold">

                                    Research Question
                                    Q<?= $questionId ?>

                                </div>

                                <h3 class="h5 mt-1 mb-0">

                                    <?= h($question['question']) ?>

                                </h3>

                                <?php
                                if (!empty($question['inferential_level'])):
                                ?>

                                    <div class="small text-muted mt-1">

                                        Inferential level:
                                        <?= h($question['inferential_level']) ?>

                                    </div>

                                <?php endif; ?>

                            </div>


                            <!-- Hypotheses -->

                            <?php foreach ($questionHypotheses as $hypothesis): ?>

                                <?php

                                $hypothesisId =
                                    (int)$hypothesis['id'];

                                $predictions =
                                    $predictionsByHypothesis[
                                        $hypothesisId
                                    ] ?? [];

                                ?>


                                <div class="card shadow-sm mb-3">

                                    <div class="card-body">


                                        <!-- Hypothesis heading -->

                                        <div class="d-flex
                                                    justify-content-between
                                                    align-items-start
                                                    gap-3
                                                    mb-3">

                                            <div class="flex-grow-1">

                                                <div class="small
                                                            text-muted
                                                            mb-1">

                                                    <strong>
                                                        H<?= $hypothesisId ?>
                                                    </strong>

                                                    <?php if (!empty($hypothesis['source']) && $hypothesis['source'] === 'brainstorming'): ?>

                                                        <span class="mx-1">·</span>

                                                        <span class="badge bg-info text-dark">
                                                            Brainstorming Session #<?= (int)$hypothesis['brainstorming_session_id'] ?>
                                                        </span>

                                                    <?php endif; ?>

                                                </div>


                                                <div class="fw-semibold fs-5">

                                                    <?= h(
                                                        $hypothesis['statement']
                                                    ) ?>

                                                </div>

                                            </div>


                                            <div class="flex-shrink-0 d-flex align-items-center gap-2">
                                                <span class="badge <?= statusBadge($hypothesis['status']) ?>">
                                                    <?= h($hypothesis['status']) ?>
                                                </span>

                                                <div class="dropdown">
                                                    <button class="btn btn-sm btn-outline-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown">
                                                        Actions
                                                    </button>
                                                    <ul class="dropdown-menu dropdown-menu-end">
                                                        <?php if ($hypothesis['status'] === 'archived'): ?>
                                                            <li>
                                                                <form method="post" action="hypotheses.php?project_id=<?= $projectId ?><?= $showArch ?>">
                                                                    <input type="hidden" name="action" value="unarchive_hypothesis">
                                                                    <input type="hidden" name="hypothesis_id" value="<?= $hypothesisId ?>">
                                                                    <button type="submit" class="dropdown-item text-success">Unarchive (Restore)</button>
                                                                </form>
                                                            </li>
                                                        <?php else: ?>
                                                            <li>
                                                                <form method="post" action="hypotheses.php?project_id=<?= $projectId ?><?= $showArch ?>">
                                                                    <input type="hidden" name="action" value="set_status">
                                                                    <input type="hidden" name="hypothesis_id" value="<?= $hypothesisId ?>">
                                                                    <input type="hidden" name="status" value="supported">
                                                                    <button type="submit" class="dropdown-item text-success">✔ Mark Supported</button>
                                                                </form>
                                                            </li>
                                                            <li>
                                                                <form method="post" action="hypotheses.php?project_id=<?= $projectId ?><?= $showArch ?>">
                                                                    <input type="hidden" name="action" value="set_status">
                                                                    <input type="hidden" name="hypothesis_id" value="<?= $hypothesisId ?>">
                                                                    <input type="hidden" name="status" value="refuted">
                                                                    <button type="submit" class="dropdown-item text-danger">✖ Mark Refuted</button>
                                                                </form>
                                                            </li>
                                                            <li>
                                                                <form method="post" action="hypotheses.php?project_id=<?= $projectId ?><?= $showArch ?>">
                                                                    <input type="hidden" name="action" value="archive_hypothesis">
                                                                    <input type="hidden" name="hypothesis_id" value="<?= $hypothesisId ?>">
                                                                    <button type="submit" class="dropdown-item text-warning">Archive / Hide</button>
                                                                </form>
                                                            </li>
                                                        <?php endif; ?>
                                                        <li><hr class="dropdown-divider"></li>
                                                        <li>
                                                            <form method="post" action="hypotheses.php?project_id=<?= $projectId ?><?= $showArch ?>">
                                                                <input type="hidden" name="action" value="delete_hypothesis">
                                                                <input type="hidden" name="hypothesis_id" value="<?= $hypothesisId ?>">
                                                                <button type="submit" class="dropdown-item text-danger" onclick="return confirm('Are you sure you want to permanently delete this hypothesis?');">Delete Permanently</button>
                                                            </form>
                                                        </li>
                                                    </ul>
                                                </div>
                                            </div>

                                        </div>


                                        <!-- Rationale -->

                                        <?php
                                        if (!empty($hypothesis['rationale'])):
                                        ?>

                                            <div class="mb-4">

                                                <div class="small
                                                            text-uppercase
                                                            text-muted
                                                            fw-semibold
                                                            mb-1">

                                                    Rationale

                                                </div>

                                                <p class="mb-0">

                                                    <?= nl2br(
                                                        h(
                                                            $hypothesis[
                                                                'rationale'
                                                            ]
                                                        )
                                                    ) ?>

                                                </p>

                                            </div>

                                        <?php endif; ?>


                                        <!-- Predictions -->

                                        <div>

                                            <div class="d-flex
                                                        justify-content-between
                                                        align-items-center
                                                        mb-2">

                                                <div class="small
                                                            text-uppercase
                                                            text-muted
                                                            fw-semibold">

                                                    Predictions

                                                </div>

                                                <span class="badge
                                                             bg-light
                                                             text-dark
                                                             border">

                                                    <?= count($predictions) ?>

                                                </span>

                                            </div>


                                            <?php if (count($predictions) === 0): ?>

                                                <p class="text-muted small mb-0">

                                                    No predictions have been
                                                    registered for this
                                                    hypothesis.

                                                </p>

                                            <?php else: ?>


                                                <?php foreach ($predictions as $prediction): ?>

                                                    <div class="prediction-item mb-2">

                                                        <div class="small text-muted">

                                                            P<?= (int)$prediction['id'] ?>

                                                        </div>

                                                        <div>

                                                            <?= h(
                                                                $prediction['statement']
                                                            ) ?>

                                                        </div>

                                                    </div>

                                                <?php endforeach; ?>


                                            <?php endif; ?>


                                        </div>


                                    </div>

                                </div>


                            <?php endforeach; ?>


                        </section>


                    <?php endforeach; ?>


                <?php endif; ?>


            </main>

        </div>

    </div>


<?php endif; ?>


<script
    src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js">
</script>


</body>
</html>
