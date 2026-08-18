<?php

declare(strict_types=1);

require_once __DIR__ . '/includes/api.php';
require_once __DIR__ . '/includes/functions.php';


/*
 * ------------------------------------------------------------
 * Load project and research questions
 * ------------------------------------------------------------
 */

$projectId = 0;
$project = null;
$questions = [];
$error = null;

$showArchived = !empty($_GET['show_archived']);
$showArch = $showArchived ? '&show_archived=1' : '';
$notice = null;

try {
    $projectId = getRequiredPositiveInt('project_id');

    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        $action = trim($_POST['action'] ?? '');
        $qId = filter_input(INPUT_POST, 'question_id', FILTER_VALIDATE_INT);

        if ($action === 'archive_question' && $qId) {
            api_patch('/questions/' . $qId, ['status' => 'archived']);
            header('Location: questions.php?project_id=' . $projectId . '&archived=1' . $showArch);
            exit;
        } elseif ($action === 'unarchive_question' && $qId) {
            api_patch('/questions/' . $qId, ['status' => 'open']);
            header('Location: questions.php?project_id=' . $projectId . '&unarchived=1' . $showArch);
            exit;
        } elseif ($action === 'mark_answered' && $qId) {
            api_patch('/questions/' . $qId, ['status' => 'answered']);
            header('Location: questions.php?project_id=' . $projectId . '&updated=1' . $showArch);
            exit;
        } elseif ($action === 'delete_question' && $qId) {
            api_delete('/questions/' . $qId);
            header('Location: questions.php?project_id=' . $projectId . '&deleted=1' . $showArch);
            exit;
        }
    }

    if (isset($_GET['archived'])) {
        $notice = 'Research question archived.';
    } elseif (isset($_GET['unarchived'])) {
        $notice = 'Research question unarchived (restored to open).';
    } elseif (isset($_GET['updated'])) {
        $notice = 'Research question status updated.';
    } elseif (isset($_GET['deleted'])) {
        $notice = 'Research question deleted.';
    }

    $project = api_get('/projects/' . $projectId);
    $rawQuestions = api_get('/projects/' . $projectId . '/questions');

    $questions = [];
    foreach ($rawQuestions as $q) {
        if (!$showArchived && ($q['status'] ?? 'open') === 'archived') {
            continue;
        }
        $questions[] = $q;
    }

} catch (Throwable $e) {
    $error = $e->getMessage();
}


/*
 * ------------------------------------------------------------
 * Current workspace menu entry
 * ------------------------------------------------------------
 */

$activePage = 'questions';


/*
 * ------------------------------------------------------------
 * Convert flat question list to parent/child structure
 *
 * Root questions use key 0.
 * Child questions use their parent_question_id as the key.
 * ------------------------------------------------------------
 */

$questionsByParent = [];

foreach ($questions as $question) {

    $parentId = $question['parent_question_id'];

    if ($parentId === null) {
        $parentId = 0;
    }

    $questionsByParent[(int)$parentId][] = $question;
}


/*
 * ------------------------------------------------------------
 * Recursive question renderer
 * ------------------------------------------------------------
 */

function renderResearchQuestions(
    array $questionsByParent,
    int $parentId = 0,
    int $depth = 0
): void {
    global $projectId, $showArch;

    if (!isset($questionsByParent[$parentId])) {
        return;
    }

    foreach ($questionsByParent[$parentId] as $question) {

        $questionId = (int)$question['id'];

        /*
         * Keep indentation bounded so very deep structures
         * do not destroy the page layout.
         */
        $indent = min($depth, 6) * 28;
        $qStatus = $question['status'] ?? 'open';
        ?>

        <div
            class="card shadow-sm mb-2"
            style="margin-left: <?= $indent ?>px;"
        >

            <div class="card-body py-3">

                <div class="d-flex
                            justify-content-between
                            align-items-start
                            gap-3">

                    <div class="flex-grow-1">

                        <div class="small text-muted mb-1">

                            <strong>
                                Q<?= $questionId ?>
                            </strong>

                            <?php if (!empty($question['inferential_level'])): ?>

                                <span class="mx-1">·</span>

                                <?= h($question['inferential_level']) ?>

                            <?php endif; ?>

                            <?php if (!empty($question['source']) && $question['source'] === 'brainstorming'): ?>

                                <span class="mx-1">·</span>

                                <span class="badge bg-info text-dark">
                                    Brainstorming Session #<?= (int)$question['brainstorming_session_id'] ?>
                                </span>

                            <?php endif; ?>

                        </div>


                        <div class="fw-semibold">

                            <?= h($question['question']) ?>

                        </div>


                        <?php if ($question['parent_question_id'] !== null): ?>

                            <div class="small text-muted mt-2">

                                Subquestion of
                                Q<?= (int)$question['parent_question_id'] ?>

                            </div>

                        <?php endif; ?>

                    </div>


                    <div class="flex-shrink-0 d-flex align-items-center gap-2">

                        <span class="badge <?= statusBadge($qStatus) ?>">
                            <?= h($qStatus) ?>
                        </span>

                        <div class="dropdown">
                            <button class="btn btn-sm btn-outline-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown">
                                Actions
                            </button>
                            <ul class="dropdown-menu dropdown-menu-end">
                                <?php if ($qStatus === 'archived'): ?>
                                    <li>
                                        <form method="post" action="questions.php?project_id=<?= $projectId ?><?= $showArch ?>">
                                            <input type="hidden" name="action" value="unarchive_question">
                                            <input type="hidden" name="question_id" value="<?= $questionId ?>">
                                            <button type="submit" class="dropdown-item text-success">Unarchive (Restore)</button>
                                        </form>
                                    </li>
                                <?php else: ?>
                                    <li>
                                        <form method="post" action="questions.php?project_id=<?= $projectId ?><?= $showArch ?>">
                                            <input type="hidden" name="action" value="mark_answered">
                                            <input type="hidden" name="question_id" value="<?= $questionId ?>">
                                            <button type="submit" class="dropdown-item">Mark as Answered</button>
                                        </form>
                                    </li>
                                    <li>
                                        <form method="post" action="questions.php?project_id=<?= $projectId ?><?= $showArch ?>">
                                            <input type="hidden" name="action" value="archive_question">
                                            <input type="hidden" name="question_id" value="<?= $questionId ?>">
                                            <button type="submit" class="dropdown-item text-warning">Archive / Hide</button>
                                        </form>
                                    </li>
                                <?php endif; ?>
                                <li><hr class="dropdown-divider"></li>
                                <li>
                                    <form method="post" action="questions.php?project_id=<?= $projectId ?><?= $showArch ?>">
                                        <input type="hidden" name="action" value="delete_question">
                                        <input type="hidden" name="question_id" value="<?= $questionId ?>">
                                        <button type="submit" class="dropdown-item text-danger" onclick="return confirm('Are you sure you want to permanently delete this research question?');">Delete Permanently</button>
                                    </form>
                                </li>
                            </ul>
                        </div>

                    </div>

                </div>

            </div>

        </div>

        <?php

        /*
         * Render child questions.
         */
        renderResearchQuestions(
            $questionsByParent,
            $questionId,
            $depth + 1
        );
    }
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
        Research Questions - Biodiversity AI Scientist
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
                Unable to load research questions
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
                 Shared research workspace navigation
                 ================================================= -->

            <?php require __DIR__ . '/includes/menu.php'; ?>


            <!-- =================================================
                 Main content
                 ================================================= -->

            <main class="col-md-9 col-lg-10 p-4">


                <div class="d-flex
                            justify-content-between
                            align-items-start
                            mb-4">

                    <div>

                        <h2 class="h3 mb-1">
                            Research Questions
                        </h2>

                        <p class="text-muted mb-0">

                            Questions and subquestions defining
                            the scientific investigation.

                        </p>

                    </div>


                    <div>

                        <span class="badge
                                     bg-light
                                     text-dark
                                     border
                                     fs-6">

                            <?= count($questions) ?>

                            question<?= count($questions) === 1 ? '' : 's' ?>

                        </span>

                    </div>

                </div>


                <?php if (count($questions) === 0): ?>


                    <!-- =========================================
                         Empty state
                         ========================================= -->

                    <div class="card shadow-sm">

                        <div class="card-body text-center py-5">

                            <h3 class="h5">
                                No research questions
                            </h3>

                            <p class="text-muted mb-0">

                                No scientific questions have yet
                                been registered for this project.

                            </p>

                        </div>

                    </div>


                <?php else: ?>


                    <!-- =========================================
                         Question hierarchy
                         ========================================= -->

                    <div class="mb-3">

                        <div class="small
                                    text-uppercase
                                    text-muted
                                    fw-semibold">

                            Question hierarchy

                        </div>

                    </div>


                    <?php

                    renderResearchQuestions(
                        $questionsByParent
                    );

                    ?>


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
