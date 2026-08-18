<?php

declare(strict_types=1);

require_once __DIR__ . '/includes/api.php';
require_once __DIR__ . '/includes/functions.php';

$projects = [];
$error = null;
$flashSuccess = null;
$showArchived = !empty($_GET['show_archived']);
$showArchParam = $showArchived ? '?show_archived=1' : '';

// Handle POST actions
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    try {
        $action = trim($_POST['action'] ?? '');
        $projectId = (int)($_POST['project_id'] ?? 0);

        if ($action === 'create_project') {
            $title = trim($_POST['title'] ?? '');
            $objective = trim($_POST['objective'] ?? '');
            if ($title === '') {
                throw new InvalidArgumentException('Project title is required.');
            }
            $newProject = api_post('/projects', [
                'title' => $title,
                'objective' => $objective !== '' ? $objective : null,
            ]);
            $newId = (int)($newProject['id'] ?? 0);
            if ($newId > 0) {
                header('Location: project.php?project_id=' . $newId);
                exit;
            }
            header('Location: projects.php?created=1');
            exit;
        }

        if ($action === 'archive_project' && $projectId > 0) {
            api_post('/projects/' . $projectId . '/archive', []);
            header('Location: projects.php' . ($showArchived ? '?show_archived=1&archived=1' : '?archived=1'));
            exit;
        }

        if ($action === 'unarchive_project' && $projectId > 0) {
            api_post('/projects/' . $projectId . '/unarchive', []);
            header('Location: projects.php' . ($showArchived ? '?show_archived=1&unarchived=1' : '?unarchived=1'));
            exit;
        }

        if ($action === 'delete_project' && $projectId > 0) {
            api_delete('/projects/' . $projectId);
            header('Location: projects.php' . ($showArchived ? '?show_archived=1&deleted=1' : '?deleted=1'));
            exit;
        }

        if ($action === 'load_demo_project') {
            $demo = api_post('/projects/seed-demo', []);
            $demoId = (int)($demo['project_id'] ?? 0);
            if ($demoId > 0) {
                header('Location: project.php?project_id=' . $demoId . '&demo_seeded=1');
                exit;
            }
            header('Location: projects.php?demo_seeded=1');
            exit;
        }

    } catch (Throwable $e) {
        $error = $e->getMessage();
    }
}

if (isset($_GET['created'])) {
    $flashSuccess = 'New research project created successfully.';
} elseif (isset($_GET['archived'])) {
    $flashSuccess = 'Project successfully archived and hidden from active view.';
} elseif (isset($_GET['unarchived'])) {
    $flashSuccess = 'Project successfully unarchived and restored to active view.';
} elseif (isset($_GET['deleted'])) {
    $flashSuccess = 'Project and all child information permanently deleted.';
}

try {
    $endpoint = '/projects' . ($showArchived ? '?include_archived=true' : '');
    $res = api_get($endpoint);
    $projects = is_array($res) ? $res : [];
} catch (Throwable $e) {
    $error = $e->getMessage();
}

?>
<!doctype html>
<html lang="en">

<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Research Projects &mdash; IdentifyShell AI Scientist</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
    <link rel="stylesheet" href="css/app.css">
</head>

<body class="bg-light">

<?php require_once __DIR__ . '/includes/navbar.php'; ?>

<div class="container py-4">

    <div class="d-flex justify-content-between align-items-center mb-4">
        <div>
            <h1 class="h3 mb-1">
                <i class="bi bi-folder2-open text-primary me-2"></i>Research Projects
            </h1>
            <p class="text-muted mb-0">
                Scientific investigations, workflows, and cumulative intelligence managed by the AI Scientist.
            </p>
        </div>

        <div class="d-flex gap-2 align-items-center">
            <!-- Filter Active vs Archived -->
            <div class="btn-group" role="group">
                <a href="projects.php" class="btn btn-sm <?= !$showArchived ? 'btn-primary' : 'btn-outline-secondary' ?>">
                    Active Projects
                </a>
                <a href="projects.php?show_archived=1" class="btn btn-sm <?= $showArchived ? 'btn-primary' : 'btn-outline-secondary' ?>">
                    Show All (Incl. Archived)
                </a>
            </div>

            <!-- New Project Button -->
            <button type="button" class="btn btn-sm btn-success" data-bs-toggle="modal" data-bs-target="#newProjectModal">
                <i class="bi bi-plus-lg me-1"></i>New Project
            </button>
        </div>
    </div>

    <?php if ($error !== null): ?>
        <div class="alert alert-danger alert-dismissible fade show">
            <strong>Error:</strong> <?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    <?php endif; ?>

    <?php if ($flashSuccess !== null): ?>
        <div class="alert alert-success alert-dismissible fade show">
            <i class="bi bi-check-circle me-1"></i> <?= htmlspecialchars($flashSuccess, ENT_QUOTES, 'UTF-8') ?>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    <?php endif; ?>

    <?php if ($error === null && count($projects) === 0): ?>
        <div class="card shadow-sm border-0">
            <div class="card-body py-5 text-center">
                <i class="bi bi-inbox text-muted display-4"></i>
                <h2 class="h5 mt-3 text-secondary">
                    <?= $showArchived ? 'No projects found in database' : 'No active research projects' ?>
                </h2>
                <p class="text-muted mb-3">
                    <?= $showArchived 
                        ? 'No projects have been registered with the AI Scientist.' 
                        : 'All projects may be archived. Click "Show All" to view archived investigations or create a new project.' ?>
                </p>
                <div class="d-flex justify-content-center gap-2 flex-wrap">
                    <button type="button" class="btn btn-primary btn-sm" data-bs-toggle="modal" data-bs-target="#newProjectModal">
                        <i class="bi bi-plus-lg me-1"></i>Create New Project
                    </button>
                    <form method="post" action="projects.php" class="d-inline">
                        <input type="hidden" name="action" value="load_demo_project">
                        <button type="submit" class="btn btn-outline-success btn-sm">
                            <i class="bi bi-magic me-1"></i>Load Example Biodiversity Project
                        </button>
                    </form>
                    <?php if (!$showArchived): ?>
                        <a href="projects.php?show_archived=1" class="btn btn-outline-secondary btn-sm">
                            View Archived Projects
                        </a>
                    <?php endif; ?>
                </div>
            </div>
        </div>
    <?php endif; ?>

    <?php if (count($projects) > 0): ?>
        <div class="card shadow-sm border-0">
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                    <thead class="table-light">
                    <tr>
                        <th style="width: 70px;">ID</th>
                        <th>Project Title & Objective</th>
                        <th style="width: 140px;">Status</th>
                        <th style="width: 180px;">Created</th>
                        <th style="width: 220px;" class="text-end">Actions</th>
                    </tr>
                    </thead>
                    <tbody>
                    <?php foreach ($projects as $project): ?>
                        <?php
                            $isArchived = ($project['status'] ?? '') === 'archived' || !empty($project['archived_at']);
                            $badgeClass = 'bg-secondary';
                            if ($project['status'] === 'active') $badgeClass = 'bg-success';
                            elseif ($project['status'] === 'draft') $badgeClass = 'bg-primary';
                            elseif ($project['status'] === 'completed') $badgeClass = 'bg-info text-dark';
                            elseif ($isArchived) $badgeClass = 'bg-warning text-dark';
                        ?>
                        <tr class="<?= $isArchived ? 'table-light text-muted' : '' ?>">
                            <td class="text-muted fw-bold">
                                #<?= (int)$project['id'] ?>
                            </td>
                            <td>
                                <div class="fw-semibold text-dark fs-6">
                                    <a href="project.php?project_id=<?= (int)$project['id'] ?>" class="text-decoration-none text-dark">
                                        <?= htmlspecialchars($project['title'], ENT_QUOTES, 'UTF-8') ?>
                                    </a>
                                </div>
                                <?php if (!empty($project['objective'])): ?>
                                    <div class="text-muted small mt-1">
                                        <?= htmlspecialchars(mb_strimwidth($project['objective'], 0, 120, '...'), ENT_QUOTES, 'UTF-8') ?>
                                    </div>
                                <?php endif; ?>
                            </td>
                            <td>
                                <span class="badge <?= $badgeClass ?> px-2 py-1">
                                    <?= htmlspecialchars(ucfirst($project['status']), ENT_QUOTES, 'UTF-8') ?>
                                </span>
                                <?php if ($isArchived): ?>
                                    <span class="badge bg-secondary-subtle text-secondary border px-1" title="Hidden from active default view">
                                        Archived
                                    </span>
                                <?php endif; ?>
                            </td>
                            <td class="text-muted small">
                                <?php
                                $created = new DateTime($project['created_at']);
                                echo htmlspecialchars($created->format('Y-m-d H:i'), ENT_QUOTES, 'UTF-8');
                                ?>
                            </td>
                            <td class="text-end">
                                <div class="btn-group" role="group">
                                    <a href="project.php?project_id=<?= (int)$project['id'] ?>" class="btn btn-sm btn-outline-primary" title="Open Workspace">
                                        <i class="bi bi-box-arrow-in-right me-1"></i>Open
                                    </a>

                                    <?php if (!$isArchived): ?>
                                        <form method="post" action="projects.php<?= $showArchParam ?>" class="d-inline" onsubmit="return confirm('Archive and hide project #<?= (int)$project['id'] ?> from the active view?');">
                                            <input type="hidden" name="action" value="archive_project">
                                            <input type="hidden" name="project_id" value="<?= (int)$project['id'] ?>">
                                            <button type="submit" class="btn btn-sm btn-outline-secondary" title="Archive / Hide Project">
                                                <i class="bi bi-archive"></i>
                                            </button>
                                        </form>
                                    <?php else: ?>
                                        <form method="post" action="projects.php<?= $showArchParam ?>" class="d-inline">
                                            <input type="hidden" name="action" value="unarchive_project">
                                            <input type="hidden" name="project_id" value="<?= (int)$project['id'] ?>">
                                            <button type="submit" class="btn btn-sm btn-outline-success" title="Unarchive / Restore Project">
                                                <i class="bi bi-arrow-counterclockwise me-1"></i>Restore
                                            </button>
                                        </form>
                                    <?php endif; ?>

                                    <?php if ($project['status'] === 'active'): ?>
                                        <button type="button" class="btn btn-sm btn-outline-secondary disabled" title="Active projects cannot be deleted. Archive the project first." disabled>
                                            <i class="bi bi-trash"></i>
                                        </button>
                                    <?php else: ?>
                                        <button type="button" class="btn btn-sm btn-outline-danger" data-bs-toggle="modal" data-bs-target="#deleteModal-<?= (int)$project['id'] ?>" title="Permanently Delete Project">
                                            <i class="bi bi-trash"></i>
                                        </button>
                                    <?php endif; ?>
                                </div>

                                <?php if ($project['status'] !== 'active'): ?>
                                    <!-- Permanent Delete Modal -->
                                    <div class="modal fade" id="deleteModal-<?= (int)$project['id'] ?>" tabindex="-1" aria-hidden="true">
                                        <div class="modal-dialog">
                                            <div class="modal-content text-start">
                                                <form method="post" action="projects.php<?= $showArchParam ?>">
                                                    <input type="hidden" name="action" value="delete_project">
                                                    <input type="hidden" name="project_id" value="<?= (int)$project['id'] ?>">
                                                    <div class="modal-header bg-danger text-white">
                                                        <h5 class="modal-title">
                                                            <i class="bi bi-exclamation-triangle-fill me-2"></i>Delete Project #<?= (int)$project['id'] ?>
                                                        </h5>
                                                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                                                    </div>
                                                    <div class="modal-body">
                                                        <p class="mb-2">
                                                            Are you sure you want to permanently delete <strong><?= htmlspecialchars($project['title'], ENT_QUOTES, 'UTF-8') ?></strong>?
                                                        </p>
                                                        <div class="alert alert-warning py-2 small mb-0">
                                                            <i class="bi bi-exclamation-circle me-1"></i>
                                                            <strong>Warning:</strong> This will delete all child entities including:
                                                            <ul class="mb-0 mt-1">
                                                                <li>Research Plans &amp; Brainstorming Sessions</li>
                                                                <li>Research Questions &amp; Hypotheses</li>
                                                                <li>Investigation Plan Generations &amp; Steps (DAGs)</li>
                                                                <li>Experiments, Analysis Runs, &amp; Results</li>
                                                                <li>Claims, Evidence Items, &amp; Reviews</li>
                                                            </ul>
                                                        </div>
                                                    </div>
                                                    <div class="modal-footer">
                                                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                                        <button type="submit" class="btn btn-danger">
                                                            <i class="bi bi-trash me-1"></i>Permanently Delete All Child Info
                                                        </button>
                                                    </div>
                                                </form>
                                            </div>
                                        </div>
                                    </div>
                                <?php endif; ?>

                            </td>
                        </tr>
                    <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
        </div>
    <?php endif; ?>

    <div class="mt-3 text-muted small d-flex justify-content-between">
        <span>
            <?= count($projects) ?> research project<?= count($projects) === 1 ? '' : 's' ?> <?= $showArchived ? '(including archived)' : '(active view)' ?>
        </span>
    </div>

</div>

<!-- Create New Project Modal -->
<div class="modal fade" id="newProjectModal" tabindex="-1" aria-labelledby="newProjectModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
            <form method="post" action="projects.php<?= $showArchParam ?>">
                <input type="hidden" name="action" value="create_project">
                <div class="modal-header bg-dark text-white">
                    <h5 class="modal-title" id="newProjectModalLabel">
                        <i class="bi bi-folder-plus text-primary me-2"></i>Create New Research Project
                    </h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div class="mb-3">
                        <label for="projectTitle" class="form-label fw-semibold">
                            Project Title <span class="text-danger">*</span>
                        </label>
                        <input type="text" class="form-control" id="projectTitle" name="title" required placeholder="e.g. Nassarius Cryptic Speciation Study">
                        <div class="form-text">A descriptive title for this biological investigation.</div>
                    </div>
                    <div class="mb-3">
                        <label for="projectObjective" class="form-label fw-semibold">
                            Research Objective <span class="text-muted fw-normal">(Optional)</span>
                        </label>
                        <textarea class="form-control" id="projectObjective" name="objective" rows="4" placeholder="e.g. Determine whether phenotypic shell variation corresponds to distinct genetic Operational Taxonomic Units (OTUs)..."></textarea>
                        <div class="form-text">The overarching objective and research questions guiding the study.</div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn btn-primary">
                        <i class="bi bi-check-lg me-1"></i>Create Project &amp; Open Workspace
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js"></script>

</body>
</html>
