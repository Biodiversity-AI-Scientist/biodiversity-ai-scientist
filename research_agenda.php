<?php

declare(strict_types=1);

require_once __DIR__ . '/includes/api.php';
require_once __DIR__ . '/includes/functions.php';

$error = null;
$flashSuccess = null;
$agendaItems = [];
$publications = [];
$literatureResults = [];
$searchQuery = trim($_GET['q'] ?? '');
$statusFilter = trim($_GET['status'] ?? '');
$typeFilter = trim($_GET['type'] ?? '');

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    try {
        $action = trim($_POST['action'] ?? '');
        
        if ($action === 'create_item') {
            $title = trim($_POST['title'] ?? '');
            $desc = trim($_POST['description'] ?? '');
            $type = trim($_POST['type'] ?? 'open_question');
            $status = trim($_POST['status'] ?? 'open');
            $evidence = trim($_POST['current_evidence'] ?? '');
            $limitations = trim($_POST['known_limitations'] ?? '');
            $followUp = trim($_POST['follow_up_opportunities'] ?? '');
            $sourceRef = trim($_POST['source_reference'] ?? '');

            if ($title === '' || $desc === '') {
                throw new InvalidArgumentException('Title and description are required.');
            }

            api_post('/research-agenda', [
                'title' => $title,
                'description' => $desc,
                'type' => $type,
                'status' => $status,
                'current_evidence' => $evidence !== '' ? $evidence : null,
                'known_limitations' => $limitations !== '' ? $limitations : null,
                'follow_up_opportunities' => $followUp !== '' ? $followUp : null,
                'source_reference' => $sourceRef !== '' ? $sourceRef : null,
            ]);

            header('Location: research_agenda.php?created=1');
            exit;
        }

        if ($action === 'update_status') {
            $itemId = (int)($_POST['item_id'] ?? 0);
            $newStatus = trim($_POST['status'] ?? '');
            if ($itemId > 0 && $newStatus !== '') {
                api_patch('/research-agenda/' . $itemId, [
                    'status' => $newStatus,
                ]);
                header('Location: research_agenda.php?updated=1');
                exit;
            }
        }
    } catch (Throwable $e) {
        $error = $e->getMessage();
    }
}

try {
    $endpoint = '/research-agenda';
    $params = [];
    if ($statusFilter !== '') {
        $params['status'] = $statusFilter;
    }
    if ($typeFilter !== '') {
        $params['type'] = $typeFilter;
    }
    if (!empty($params)) {
        $endpoint .= '?' . http_build_query($params);
    }
    $agendaItems = api_get($endpoint);

    // Fetch FindShell publications
    $pubData = api_get('/research-program/publications');
    $publications = $pubData['publications'] ?? [];

    // If search requested, query remote Papers API
    if ($searchQuery !== '') {
        $litData = api_get('/research-program/literature-search?q=' . urlencode($searchQuery) . '&limit=6');
        $literatureResults = $litData['results'] ?? [];
    }
} catch (Throwable $e) {
    if ($error === null) {
        $error = $e->getMessage();
    }
}

if (isset($_GET['created'])) {
    $flashSuccess = 'New Research Agenda item recorded in the cumulative science registry.';
} elseif (isset($_GET['updated'])) {
    $flashSuccess = 'Research agenda item status updated successfully.';
}

$activePage = 'research_agenda';

function typeBadge(string $type): string {
    return match ($type) {
        'open_question' => 'bg-primary',
        'methodological_issue' => 'bg-warning text-dark',
        'cross_study_hypothesis' => 'bg-info text-dark',
        'replication_need' => 'bg-danger',
        'limitation' => 'bg-secondary',
        'research_opportunity' => 'bg-success',
        default => 'bg-dark',
    };
}

function agendaStatusBadge(string $status): string {
    return match ($status) {
        'open' => 'bg-danger',
        'investigating' => 'bg-warning text-dark',
        'partially_resolved' => 'bg-info text-dark',
        'resolved' => 'bg-success',
        default => 'bg-secondary',
    };
}
?>
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Research Agenda & Program Intelligence - Biodiversity AI Scientist</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="css/app.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
</head>
<body class="bg-light">


<?php require_once __DIR__ . '/includes/navbar.php'; ?>

<div class="container-fluid py-4 px-lg-5">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <div>
            <h1 class="h3 mb-1">Cumulative Science: Research Program Intelligence</h1>
            <p class="text-muted mb-0">Cross-study state, open methodological questions, and multi-source scientific memory.</p>
        </div>
        <div>
            <button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#newAgendaModal">
                + New Agenda Item
            </button>
        </div>
    </div>

    <?php if ($flashSuccess !== null): ?>
        <div class="alert alert-success alert-dismissible fade show" role="alert">
            <?= h($flashSuccess) ?>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    <?php endif; ?>

    <?php if ($error !== null): ?>
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
            <?= h($error) ?>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    <?php endif; ?>

    <div class="row g-4">
        <!-- Main Column: Research Agenda Items -->
        <div class="col-lg-8">
            <!-- Filter Bar -->
            <div class="card shadow-sm mb-4">
                <div class="card-body p-3">
                    <form method="get" class="row g-2 align-items-center">
                        <div class="col-auto">
                            <label class="small fw-semibold text-muted">Status:</label>
                            <select name="status" class="form-select form-select-sm" onchange="this.form.submit()">
                                <option value="">All Statuses</option>
                                <option value="open" <?= $statusFilter === 'open' ? 'selected' : '' ?>>Open</option>
                                <option value="investigating" <?= $statusFilter === 'investigating' ? 'selected' : '' ?>>Investigating</option>
                                <option value="partially_resolved" <?= $statusFilter === 'partially_resolved' ? 'selected' : '' ?>>Partially Resolved</option>
                                <option value="resolved" <?= $statusFilter === 'resolved' ? 'selected' : '' ?>>Resolved</option>
                            </select>
                        </div>
                        <div class="col-auto">
                            <label class="small fw-semibold text-muted">Type:</label>
                            <select name="type" class="form-select form-select-sm" onchange="this.form.submit()">
                                <option value="">All Types</option>
                                <option value="open_question" <?= $typeFilter === 'open_question' ? 'selected' : '' ?>>Open Question</option>
                                <option value="methodological_issue" <?= $typeFilter === 'methodological_issue' ? 'selected' : '' ?>>Methodological Issue</option>
                                <option value="cross_study_hypothesis" <?= $typeFilter === 'cross_study_hypothesis' ? 'selected' : '' ?>>Cross-Study Hypothesis</option>
                                <option value="limitation" <?= $typeFilter === 'limitation' ? 'selected' : '' ?>>Limitation</option>
                                <option value="research_opportunity" <?= $typeFilter === 'research_opportunity' ? 'selected' : '' ?>>Research Opportunity</option>
                            </select>
                        </div>
                        <?php if ($statusFilter !== '' || $typeFilter !== ''): ?>
                            <div class="col-auto pt-3">
                                <a href="research_agenda.php" class="btn btn-sm btn-outline-secondary">Reset</a>
                            </div>
                        <?php endif; ?>
                    </form>
                </div>
            </div>

            <!-- Agenda Items List -->
            <div class="card shadow-sm mb-4">
                <div class="card-header bg-white fw-bold d-flex justify-content-between align-items-center">
                    <span>Program Agenda Questions & Hypotheses (<?= count($agendaItems) ?>)</span>
                </div>
                <div class="card-body p-0">
                    <?php if (empty($agendaItems)): ?>
                        <div class="p-4 text-center text-muted">No agenda items matching filter.</div>
                    <?php else: ?>
                        <div class="list-group list-group-flush">
                            <?php foreach ($agendaItems as $item): ?>
                                <div class="list-group-item p-4">
                                    <div class="d-flex justify-content-between align-items-start mb-2">
                                        <div>
                                            <span class="badge <?= typeBadge($item['type']) ?> me-1"><?= h(str_replace('_', ' ', $item['type'])) ?></span>
                                            <span class="badge <?= agendaStatusBadge($item['status']) ?>"><?= h(str_replace('_', ' ', $item['status'])) ?></span>
                                            <h2 class="h5 mt-2 mb-1"><?= h($item['title']) ?></h2>
                                        </div>
                                        <div class="dropdown">
                                            <button class="btn btn-sm btn-outline-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown">
                                                Status
                                            </button>
                                            <ul class="dropdown-menu dropdown-menu-end">
                                                <li>
                                                    <form method="post">
                                                        <input type="hidden" name="action" value="update_status">
                                                        <input type="hidden" name="item_id" value="<?= (int)$item['id'] ?>">
                                                        <input type="hidden" name="status" value="open">
                                                        <button type="submit" class="dropdown-item">Mark Open</button>
                                                    </form>
                                                </li>
                                                <li>
                                                    <form method="post">
                                                        <input type="hidden" name="action" value="update_status">
                                                        <input type="hidden" name="item_id" value="<?= (int)$item['id'] ?>">
                                                        <input type="hidden" name="status" value="investigating">
                                                        <button type="submit" class="dropdown-item">Mark Investigating</button>
                                                    </form>
                                                </li>
                                                <li>
                                                    <form method="post">
                                                        <input type="hidden" name="action" value="update_status">
                                                        <input type="hidden" name="item_id" value="<?= (int)$item['id'] ?>">
                                                        <input type="hidden" name="status" value="partially_resolved">
                                                        <button type="submit" class="dropdown-item">Mark Partially Resolved</button>
                                                    </form>
                                                </li>
                                                <li>
                                                    <form method="post">
                                                        <input type="hidden" name="action" value="update_status">
                                                        <input type="hidden" name="item_id" value="<?= (int)$item['id'] ?>">
                                                        <input type="hidden" name="status" value="resolved">
                                                        <button type="submit" class="dropdown-item">Mark Resolved</button>
                                                    </form>
                                                </li>
                                            </ul>
                                        </div>
                                    </div>

                                    <p class="text-secondary mb-3"><?= h($item['description']) ?></p>

                                    <div class="row g-2 small">
                                        <?php if (!empty($item['current_evidence'])): ?>
                                            <div class="col-md-6">
                                                <div class="p-2 bg-light rounded border">
                                                    <strong class="text-success">Current Evidence:</strong>
                                                    <div class="text-muted mt-1"><?= h($item['current_evidence']) ?></div>
                                                </div>
                                            </div>
                                        <?php endif; ?>
                                        <?php if (!empty($item['follow_up_opportunities'])): ?>
                                            <div class="col-md-6">
                                                <div class="p-2 bg-light rounded border">
                                                    <strong class="text-primary">Follow-up Opportunity:</strong>
                                                    <div class="text-muted mt-1"><?= h($item['follow_up_opportunities']) ?></div>
                                                </div>
                                            </div>
                                        <?php endif; ?>
                                    </div>

                                    <?php if (!empty($item['source_reference'])): ?>
                                        <div class="mt-2 text-muted small">
                                            <em>Source: <?= h($item['source_reference']) ?></em>
                                        </div>
                                    <?php endif; ?>
                                </div>
                            <?php endforeach; ?>
                        </div>
                    <?php endif; ?>
                </div>
            </div>
        </div>

        <!-- Right Column: Multi-Source Scientific Memory -->
        <div class="col-lg-4">
            <!-- Literature Search Widget -->
            <div class="card shadow-sm mb-4">
                <div class="card-header bg-white fw-bold d-flex justify-content-between align-items-center">
                    <span>Literature Search</span>
                    <span class="badge bg-secondary">Papers API</span>
                </div>
                <div class="card-body p-3">
                    <form method="get" class="mb-3">
                        <div class="input-group input-group-sm">
                            <input type="text" name="q" class="form-control" placeholder="Search papers (e.g. Nassarius, Conus)..." value="<?= h($searchQuery) ?>">
                            <button type="submit" class="btn btn-outline-primary">Search</button>
                        </div>
                    </form>

                    <?php if ($searchQuery !== ''): ?>
                        <h3 class="h6 fw-bold">Results for "<?= h($searchQuery) ?>" (<?= count($literatureResults) ?>):</h3>
                        <?php if (empty($literatureResults)): ?>
                            <p class="text-muted small">No indexed papers found for this query.</p>
                        <?php else: ?>
                            <div class="list-group list-group-flush small">
                                <?php foreach ($literatureResults as $paper): ?>
                                    <div class="list-group-item px-0 py-2 border-bottom">
                                        <div class="fw-bold"><?= h($paper['title'] ?? 'Untitled') ?></div>
                                        <div class="text-muted">
                                            <?= h($paper['authors'] ?? 'Unknown') ?> (<?= h((string)($paper['year'] ?? 'N/D')) ?>)
                                        </div>
                                        <div class="badge bg-light text-dark border mt-1">ID: <?= h($paper['paper_id'] ?? '') ?></div>
                                    </div>
                                <?php endforeach; ?>
                            </div>
                        <?php endif; ?>
                    <?php else: ?>
                        <p class="text-muted small mb-0">Search the indexed scientific papers repository for empirical benchmarks and citations.</p>
                    <?php endif; ?>
                </div>
            </div>

            <!-- Publications Index -->
            <div class="card shadow-sm">
                <div class="card-header bg-white fw-bold d-flex justify-content-between align-items-center">
                    <span>FindShell Publications</span>
                    <span class="badge bg-info text-dark">FindShell Index</span>
                </div>
                <div class="card-body p-3 small" style="max-height: 480px; overflow-y: auto;">
                    <p class="text-muted mb-2">Technical reports and research papers published across the FindShell research program:</p>
                    <ul class="list-unstyled mb-0">
                        <?php foreach ($publications as $pub): ?>
                            <li class="mb-2 pb-2 border-bottom">
                                <a href="<?= h($pub['url']) ?>" target="_blank" class="text-decoration-none fw-semibold">
                                    📄 <?= h($pub['title']) ?>
                                </a>
                            </li>
                        <?php endforeach; ?>
                    </ul>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Modal: New Research Agenda Item -->
<div class="modal fade" id="newAgendaModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <form method="post">
                <input type="hidden" name="action" value="create_item">
                <div class="modal-header">
                    <h5 class="modal-title">Record Research Agenda Item</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="mb-3">
                        <label class="form-label fw-bold">Title</label>
                        <input type="text" name="title" class="form-control" required placeholder="e.g. Cross-genus variation in few-shot classification">
                    </div>
                    <div class="row g-3 mb-3">
                        <div class="col-md-6">
                            <label class="form-label fw-bold">Type</label>
                            <select name="type" class="form-select">
                                <option value="open_question">Open Question</option>
                                <option value="methodological_issue">Methodological Issue</option>
                                <option value="cross_study_hypothesis">Cross-Study Hypothesis</option>
                                <option value="limitation">Limitation</option>
                                <option value="research_opportunity">Research Opportunity</option>
                            </select>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label fw-bold">Initial Status</label>
                            <select name="status" class="form-select">
                                <option value="open">Open</option>
                                <option value="investigating">Investigating</option>
                                <option value="partially_resolved">Partially Resolved</option>
                                <option value="resolved">Resolved</option>
                            </select>
                        </div>
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-bold">Description</label>
                        <textarea name="description" class="form-control" rows="3" required placeholder="Detailed description of the unresolved problem or cross-study question..."></textarea>
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-bold">Current Evidence / State of Knowledge</label>
                        <textarea name="current_evidence" class="form-control" rows="2" placeholder="What is currently known from previous studies..."></textarea>
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-bold">Follow-Up Opportunities (Datasets / Taxa / Architectures)</label>
                        <textarea name="follow_up_opportunities" class="form-control" rows="2" placeholder="What next experiments or candidate taxa would test this..."></textarea>
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-bold">Source Reference (Publication / URL / Study)</label>
                        <input type="text" name="source_reference" class="form-control" placeholder="e.g. FindShell Blog Dec 2024">
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn btn-primary">Save to Research Agenda</button>
                </div>
            </form>
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
