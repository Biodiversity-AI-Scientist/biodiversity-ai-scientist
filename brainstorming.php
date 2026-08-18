<?php

declare(strict_types=1);

require_once __DIR__ . '/includes/api.php';
require_once __DIR__ . '/includes/functions.php';

$projectId = 0;
$project = null;
$sessions = [];
$projectQuestions = [];
$sessionPlans = [];
$selectedSession = null;
$selectedSessionId = 0;
$error = null;
$flashSuccess = null;
$lastContent = '';
$lastInitialIdea = '';

// Process POST actions
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    try {
        $projectId = getRequiredPositiveInt('project_id');
        $action = trim($_POST['action'] ?? '');

        if ($action === 'create_session') {
            $initialIdea = trim($_POST['initial_idea'] ?? '');
            $lastInitialIdea = $initialIdea;
            if ($initialIdea === '') {
                throw new InvalidArgumentException('Initial research idea cannot be empty.');
            }

            $newSession = api_post('/brainstorming-sessions', [
                'project_id' => $projectId,
                'initial_idea' => $initialIdea,
                'status' => 'active',
                'messages' => [
                    [
                        'role' => 'user',
                        'content' => $initialIdea,
                        'timestamp' => date('c'),
                    ]
                ]
            ]);

            header('Location: brainstorming.php?project_id=' . $projectId . '&session_id=' . $newSession['id'] . '&created=1');
            exit;
        }

        if ($action === 'add_message') {
            $sessionId = (int)($_POST['session_id'] ?? 0);
            $role = trim($_POST['role'] ?? 'user');
            $content = trim($_POST['content'] ?? '');
            $lastContent = $content;

            if ($sessionId <= 0 || $content === '') {
                throw new InvalidArgumentException('Session ID and message content are required.');
            }

            api_post('/brainstorming-sessions/' . $sessionId . '/messages', [
                'role' => $role,
                'content' => $content,
                'timestamp' => date('c')
            ]);

            header('Location: brainstorming.php?project_id=' . $projectId . '&session_id=' . $sessionId);
            exit;
        }

        if ($action === 'generate_plan') {
            $sessionId = (int)($_POST['session_id'] ?? 0);
            if ($sessionId <= 0) {
                throw new InvalidArgumentException('Session ID is required.');
            }

            $plan = api_post('/brainstorming-sessions/' . $sessionId . '/research-plan', []);
            header('Location: brainstorming.php?project_id=' . $projectId . '&session_id=' . $sessionId . '&plan_generated=1');
            exit;
        }

        if ($action === 'revise_plan') {
            $sessionId = (int)($_POST['session_id'] ?? 0);
            $planId = (int)($_POST['plan_id'] ?? 0);
            $steering = trim($_POST['steering_instructions'] ?? '');

            if ($planId <= 0 || $steering === '') {
                throw new InvalidArgumentException('Plan ID and steering instructions are required.');
            }

            $revised = api_post('/research-plans/' . $planId . '/revise', [
                'steering_instructions' => $steering
            ]);

            header('Location: brainstorming.php?project_id=' . $projectId . '&session_id=' . $sessionId . '&plan_revised=1');
            exit;
        }

        if ($action === 'approve_plan') {
            $sessionId = (int)($_POST['session_id'] ?? 0);
            $planId = (int)($_POST['plan_id'] ?? 0);

            if ($planId <= 0) {
                throw new InvalidArgumentException('Plan ID is required.');
            }

            api_post('/research-plans/' . $planId . '/approve', []);
            header('Location: brainstorming.php?project_id=' . $projectId . '&session_id=' . $sessionId . '&plan_approved=1');
            exit;
        }

        if ($action === 'promote_question') {
            $sessionId = (int)($_POST['session_id'] ?? 0);
            $questionText = trim($_POST['question'] ?? '');
            $inferentialLevel = trim($_POST['inferential_level'] ?? '');

            if ($questionText === '') {
                throw new InvalidArgumentException('Question text is required.');
            }

            $newQ = api_post('/projects/' . $projectId . '/questions', [
                'question' => $questionText,
                'inferential_level' => $inferentialLevel !== '' ? $inferentialLevel : null,
                'source' => 'brainstorming',
                'brainstorming_session_id' => $sessionId > 0 ? $sessionId : null,
            ]);

            header('Location: brainstorming.php?project_id=' . $projectId . '&session_id=' . $sessionId . '&promoted_q=' . $newQ['id']);
            exit;
        }

        if ($action === 'promote_hypothesis') {
            $sessionId = (int)($_POST['session_id'] ?? 0);
            $questionId = (int)($_POST['question_id'] ?? 0);
            $statement = trim($_POST['statement'] ?? '');
            $rationale = trim($_POST['rationale'] ?? '');

            if ($questionId <= 0 || $statement === '') {
                throw new InvalidArgumentException('Target Research Question and Hypothesis statement are required.');
            }

            $newH = api_post('/questions/' . $questionId . '/hypotheses', [
                'statement' => $statement,
                'rationale' => $rationale !== '' ? $rationale : null,
                'source' => 'brainstorming',
                'brainstorming_session_id' => $sessionId > 0 ? $sessionId : null,
            ]);

            header('Location: brainstorming.php?project_id=' . $projectId . '&session_id=' . $sessionId . '&promoted_h=' . $newH['id']);
            exit;
        }

        if ($action === 'reject_candidate') {
            $sessionId = (int)($_POST['session_id'] ?? 0);
            $candidateType = trim($_POST['candidate_type'] ?? 'candidate');
            $candidateText = trim($_POST['candidate_text'] ?? '');
            $reason = trim($_POST['reason'] ?? '');

            if ($sessionId <= 0 || $candidateText === '') {
                throw new InvalidArgumentException('Session ID and candidate text are required.');
            }

            $note = "[Audit] Rejected Candidate (" . ucfirst($candidateType) . "): \"" . $candidateText . "\"";
            if ($reason !== '') {
                $note .= " | Rejection Reason: " . $reason;
            }

            api_post('/brainstorming-sessions/' . $sessionId . '/messages?generate_llm_response=false', [
                'role' => 'user',
                'content' => $note,
                'timestamp' => date('c')
            ]);



            header('Location: brainstorming.php?project_id=' . $projectId . '&session_id=' . $sessionId . '&rejected=1');
            exit;
        }

        if ($action === 'update_session') {
            $sessionId = (int)($_POST['session_id'] ?? 0);
            $status = trim($_POST['status'] ?? '');
            $planTitle = trim($_POST['plan_title'] ?? '');

            if ($sessionId <= 0) {
                throw new InvalidArgumentException('Session ID is required.');
            }

            $updateData = [];
            if ($status !== '') {
                $updateData['status'] = $status;
            }

            if (!empty($updateData)) {
                api_patch('/brainstorming-sessions/' . $sessionId, $updateData);
            }

            header('Location: brainstorming.php?project_id=' . $projectId . '&session_id=' . $sessionId);
            exit;
        }

        if ($action === 'archive_session') {
            $sessionId = (int)($_POST['session_id'] ?? 0);
            if ($sessionId <= 0) {
                throw new InvalidArgumentException('Session ID is required.');
            }

            api_patch('/brainstorming-sessions/' . $sessionId . '/archive');
            $showArch = !empty($_GET['show_archived']) ? '&show_archived=1' : '';
            header('Location: brainstorming.php?project_id=' . $projectId . '&archived=1' . $showArch);
            exit;
        }

        if ($action === 'unarchive_session') {
            $sessionId = (int)($_POST['session_id'] ?? 0);
            if ($sessionId <= 0) {
                throw new InvalidArgumentException('Session ID is required.');
            }

            api_patch('/brainstorming-sessions/' . $sessionId . '/unarchive');
            $showArch = !empty($_GET['show_archived']) ? '&show_archived=1' : '';
            header('Location: brainstorming.php?project_id=' . $projectId . '&session_id=' . $sessionId . '&unarchived=1' . $showArch);
            exit;
        }
    } catch (Throwable $e) {
        $error = $e->getMessage();
    }
}

// Fetch Page Data
$showArchived = !empty($_GET['show_archived']);
try {
    if ($projectId === 0) {
        $projectId = getRequiredPositiveInt('project_id');
    }

    $project = api_get('/projects/' . $projectId);
    $sessions = api_get('/projects/' . $projectId . '/brainstorming-sessions?include_archived=' . ($showArchived ? 'true' : 'false'));
    $projectQuestions = api_get('/projects/' . $projectId . '/questions');
    $projectHypotheses = [];
    try {
        $projectHypotheses = api_get('/projects/' . $projectId . '/hypotheses');
    } catch (Throwable $e) {
        $projectHypotheses = [];
    }
    $programAgenda = [];
    try {
        $programAgenda = api_get('/research-agenda?limit=5');
    } catch (Throwable $e) {}


    $requestedSessionId = isset($_GET['session_id']) ? (int)$_GET['session_id'] : 0;
    if ($requestedSessionId > 0) {
        $selectedSessionId = $requestedSessionId;
    } elseif (!empty($sessions)) {
        $selectedSessionId = (int)$sessions[0]['id'];
    }

    if ($selectedSessionId > 0) {
        $selectedSession = api_get('/brainstorming-sessions/' . $selectedSessionId);
        $allProjectPlans = api_get('/projects/' . $projectId . '/research-plans?include_archived=' . ($showArchived ? 'true' : 'false'));
        foreach ($allProjectPlans as $pl) {
            if (isset($pl['brainstorming_session_id']) && (int)$pl['brainstorming_session_id'] === $selectedSessionId) {
                $sessionPlans[] = $pl;
            }
        }
    }
    try {
        $llmStatus = api_get('/llm-gateway/status');
    } catch (Throwable $ignore) {
        $llmStatus = null;
    }
} catch (Throwable $e) {
    if ($error === null) {
        $error = $e->getMessage();
    }
}

if (isset($_GET['created']) && $_GET['created'] === '1') {
    $flashSuccess = 'Brainstorming session created successfully.';
} elseif (isset($_GET['promoted_q'])) {
    $flashSuccess = 'Research Question Q' . (int)$_GET['promoted_q'] . ' accepted and added to project with full session provenance!';
} elseif (isset($_GET['promoted_h'])) {
    $flashSuccess = 'Hypothesis H' . (int)$_GET['promoted_h'] . ' accepted and attached to Research Question with session provenance!';
} elseif (isset($_GET['rejected'])) {
    $flashSuccess = 'Candidate suggestion marked as rejected and rationale recorded for auditability.';
} elseif (isset($_GET['plan_generated'])) {
    $flashSuccess = 'Structured Research Plan generated successfully from brainstorming session!';
} elseif (isset($_GET['plan_revised'])) {
    $flashSuccess = 'Research Plan revised with AI steering instructions. New plan version generated!';
} elseif (isset($_GET['plan_approved'])) {
    $flashSuccess = 'Research Plan approved successfully!';
} elseif (isset($_GET['archived'])) {
    $flashSuccess = 'Brainstorming session archived/hidden from active list.';
} elseif (isset($_GET['unarchived'])) {
    $flashSuccess = 'Brainstorming session unarchived and restored to active state.';
}


$activePage = 'brainstorming';

// Helper function to extract candidates per message content
function extractCandidatesFromText(string $content): array {
    $suggestedQuestions = [];
    $candidateHypotheses = [];

    $lines = explode("\n", $content);
    $currentSection = null;

    foreach ($lines as $line) {
        $trimmed = trim($line);
        if (stristr($trimmed, 'Suggested Research Questions:')) {
            $currentSection = 'questions';
            continue;
        } elseif (stristr($trimmed, 'Candidate Hypotheses:')) {
            $currentSection = 'hypotheses';
            continue;
        }

        if ($trimmed === '' || str_starts_with($trimmed, '#')) {
            continue;
        }

        if ($currentSection === 'questions') {
            if (preg_match('/^(?:[-*•]|\d+\.)\s*(.+)$/', $trimmed, $m)) {
                $item = trim($m[1]);
                if (!in_array($item, $suggestedQuestions, true)) {
                    $suggestedQuestions[] = $item;
                }
            }
        } elseif ($currentSection === 'hypotheses') {
            if (preg_match('/^(?:[-*•]|H\d+:|\d+\.)\s*(.+)$/', $trimmed, $m)) {
                $item = trim($m[1]);
                if (!in_array($item, $candidateHypotheses, true)) {
                    $candidateHypotheses[] = $item;
                }
            }
        }
    }

    return [
        'questions' => $suggestedQuestions,
        'hypotheses' => $candidateHypotheses,
    ];
}

$latestPlan = !empty($sessionPlans) ? $sessionPlans[0] : null;

?>
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Brainstorming - Biodiversity AI Scientist</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="css/app.css" rel="stylesheet">
    <style>
        .chat-bubble-user {
            background-color: #e9ecef;
            border-left: 4px solid #0d6efd;
        }
        .chat-bubble-assistant {
            background-color: #f8f9fa;
            border-left: 4px solid #198754;
        }
        .chat-bubble-system {
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
        }
    </style>
</head>
<body class="bg-light">

<!-- Navbar -->
<?php require_once __DIR__ . '/includes/navbar.php'; ?>


<?php if ($error !== null && $project === null): ?>
    <div class="container py-5">
        <div class="alert alert-danger">
            <h1 class="h5">Unable to load project workspace</h1>
            <p class="mb-3"><?= h($error) ?></p>
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
                        <div class="text-muted small mb-1">
                            Research Project #<?= (int)$project['id'] ?>
                        </div>
                        <h1 class="h4 mb-1"><?= h($project['title']) ?></h1>
                        <?php if (!empty($project['objective'])): ?>
                            <div class="text-muted small mt-1">
                                <i class="bi bi-card-text text-primary me-1"></i><?= h($project['objective']) ?>
                            </div>
                        <?php endif; ?>
                    </div>
                    <div>
                        <a href="project.php?project_id=<?= $projectId ?>" class="btn btn-sm btn-outline-secondary">
                            Project overview
                        </a>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <!-- Sidebar Navigation -->
            <?php require __DIR__ . '/includes/menu.php'; ?>

            <!-- Main Content Area -->
            <main class="col-md-9 col-lg-10 p-4">

                <?php if ($error !== null): ?>
                    <div class="alert alert-danger alert-dismissible fade show" role="alert">
                        <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
                            <div>
                                <strong>Query Error:</strong> <?= h($error) ?>
                                <?php if ($lastContent !== ''): ?>
                                    <div class="small mt-1">Your message has been preserved below. Click <strong>Retry Query</strong> to try again.</div>
                                <?php endif; ?>
                            </div>
                            <?php if (!empty($lastContent) && $selectedSessionId > 0): ?>
                                <form method="post" action="brainstorming.php?project_id=<?= $projectId ?>&session_id=<?= $selectedSessionId ?>" class="ms-auto" onsubmit="handleFormSubmit(this)">
                                    <input type="hidden" name="action" value="add_message">
                                    <input type="hidden" name="project_id" value="<?= $projectId ?>">
                                    <input type="hidden" name="session_id" value="<?= $selectedSessionId ?>">
                                    <input type="hidden" name="role" value="user">
                                    <input type="hidden" name="content" value="<?= h($lastContent) ?>">
                                    <button type="submit" class="btn btn-sm btn-danger text-nowrap">
                                        Retry Query
                                    </button>
                                </form>
                            <?php endif; ?>
                        </div>
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                <?php endif; ?>

                <?php if (!empty($llmStatus) && empty($llmStatus['configured'])): ?>
                    <div class="alert alert-warning d-flex align-items-center mb-3 shadow-sm border-warning" role="alert">
                        <i class="bi bi-key-fill fs-4 me-3 text-warning"></i>
                        <div>
                            <strong>LLM Gateway Not Configured:</strong> Automated AI brainstorming requires an LLM API key.
                            Add your API key to your <code>.env</code> file or visit the <a href="configuration.php" class="alert-link">Configuration Page</a>.
                        </div>
                    </div>
                <?php endif; ?>

                <?php if ($flashSuccess !== null): ?>
                    <div class="alert alert-success alert-dismissible fade show" role="alert">
                        <?= h($flashSuccess) ?>
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                <?php endif; ?>

                <div class="d-flex justify-content-between align-items-center mb-4">
                    <div>
                        <h2 class="h3 mb-1">Interactive Brainstorming</h2>
                        <p class="text-muted mb-0">Brainstorm freely; promote selectively. Formulate questions & hypotheses with persistent provenance.</p>
                    </div>
                    <div class="d-flex gap-2">
                        <a href="help/brainstorming.php?project_id=<?= $projectId ?>" class="btn btn-outline-info">
                            📖 Help &amp; Guide
                        </a>
                        <button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#newSessionModal">
                            + New Brainstorming Session
                        </button>
                    </div>
                </div>

                <?php if (empty($sessions)): ?>
                    <!-- Empty State -->
                    <div class="card shadow-sm">
                        <div class="card-body text-center py-5">
                            <h3 class="h5 mb-2">No Brainstorming Sessions Yet</h3>
                            <p class="text-muted mb-4">Start an interactive session to brainstorm research questions, refine hypotheses, and draft scientific plans.</p>
                            <button type="button" class="btn btn-primary btn-lg" data-bs-toggle="modal" data-bs-target="#newSessionModal">
                                Start First Session
                            </button>
                        </div>
                    </div>
                <?php else: ?>

                    <div class="row g-4">
                        <!-- Session Selector List (Left Column) -->
                        <div class="col-lg-4">
                            <div class="card shadow-sm mb-4">
                                <div class="card-header bg-white fw-bold d-flex justify-content-between align-items-center">
                                    <span>Sessions (<?= count($sessions) ?>)</span>
                                    <a href="brainstorming.php?project_id=<?= $projectId ?>&show_archived=<?= $showArchived ? '0' : '1' ?><?= $selectedSessionId > 0 ? '&session_id=' . $selectedSessionId : '' ?>"
                                       class="btn btn-sm btn-link p-0 text-decoration-none small text-secondary">
                                        <?= $showArchived ? 'Hide Archived' : 'Show Archived' ?>
                                    </a>
                                </div>
                                <div class="list-group list-group-flush">
                                    <?php foreach ($sessions as $s): ?>
                                        <?php
                                            $isCurrent = ((int)$s['id'] === $selectedSessionId);
                                            $badgeClass = 'bg-primary';
                                            if ($s['status'] === 'completed') $badgeClass = 'bg-success';
                                            if ($s['status'] === 'archived') $badgeClass = 'bg-secondary';
                                        ?>
                                        <a href="brainstorming.php?project_id=<?= $projectId ?>&session_id=<?= (int)$s['id'] ?><?= $showArchived ? '&show_archived=1' : '' ?>"
                                           class="list-group-item list-group-item-action <?= $isCurrent ? 'active' : '' ?>">
                                            <div class="d-flex justify-content-between align-items-center mb-1">
                                                <span class="fw-semibold">Session #<?= (int)$s['id'] ?></span>
                                                <span class="badge <?= $badgeClass ?>"><?= h($s['status']) ?></span>
                                            </div>
                                            <div class="text-truncate small <?= $isCurrent ? 'text-white-50' : 'text-muted' ?>">
                                                <?= h($s['initial_idea']) ?>
                                            </div>
                                            <div class="small mt-1 text-end <?= $isCurrent ? 'text-white-50' : 'text-muted' ?>">
                                                <?= count($s['messages'] ?? []) ?> msgs
                                            </div>
                                        </a>
                                    <?php endforeach; ?>
                                </div>
                            </div>

                            <!-- Cumulative Science: Program Agenda Items -->
                            <div class="card shadow-sm mb-4">
                                <div class="card-header bg-white fw-bold d-flex justify-content-between align-items-center">
                                    <span>Program Agenda (Cumulative)</span>
                                    <a href="research_agenda.php" class="small text-decoration-none">View All &rarr;</a>
                                </div>
                                <div class="card-body p-3 small">
                                    <?php if (empty($programAgenda)): ?>
                                        <p class="text-muted mb-0">No active research agenda items recorded.</p>
                                    <?php else: ?>
                                        <ul class="list-unstyled mb-0">
                                            <?php foreach ($programAgenda as $ag): ?>
                                                <li class="mb-2 pb-2 border-bottom">
                                                    <span class="badge bg-light text-dark border"><?= h(str_replace('_', ' ', $ag['type'])) ?></span>
                                                    <div class="fw-bold text-dark mt-1"><?= h($ag['title']) ?></div>
                                                    <div class="text-muted mt-1 text-truncate"><?= h($ag['description']) ?></div>
                                                </li>
                                            <?php endforeach; ?>
                                        </ul>
                                    <?php endif; ?>
                                </div>
                            </div>

                            <!-- Domain & Literature Intelligence (WoRMS, arXiv, bioRxiv) -->
                            <div class="card shadow-sm mb-4">
                                <div class="card-header bg-white fw-bold d-flex justify-content-between align-items-center">
                                    <span>Domain & Literature Intel</span>
                                    <button type="button" class="btn btn-sm btn-link p-0 text-decoration-none small text-primary" data-bs-toggle="modal" data-bs-target="#compareTaxaModal">
                                        Compare Taxa &rarr;
                                    </button>
                                </div>
                                <div class="card-body p-3 small">
                                    <div class="text-muted mb-2">
                                        Grounding against <strong>WoRMS</strong>, <strong>arXiv (cs.CV)</strong>, and local scientific literature index.
                                    </div>
                                    <div class="p-2 bg-light rounded border mb-2">
                                        <div class="fw-semibold text-dark">WoRMS Taxonomic Status</div>
                                        <div class="text-muted small">Live validation of accepted genus nomenclature & synonyms.</div>
                                    </div>
                                    <div class="p-2 bg-light rounded border">
                                        <div class="fw-semibold text-dark">Cryptic Complex Triage</div>
                                        <div class="text-muted small">Morphological overlap & molecular classification flags.</div>
                                    </div>
                                </div>
                            </div>

                            <!-- Adaptive Research Intelligence (v2 Orchestrator) -->
                            <div class="card shadow-sm mb-4 border-primary">
                                <div class="card-header bg-primary text-white fw-bold d-flex justify-content-between align-items-center py-2">
                                    <span>Adaptive Intelligence v2</span>
                                    <button type="button" class="btn btn-sm btn-light py-0 px-2 small fw-bold text-primary" data-bs-toggle="modal" data-bs-target="#inspectOrchestratorModal">
                                        Inspect &rarr;
                                    </button>
                                </div>
                                <div class="card-body p-3 small bg-light">
                                    <div class="text-muted mb-2">
                                        Dynamically routes questions across <strong>Data</strong>, <strong>Program</strong>, and <strong>Domain</strong> layers with strict 4-way provenance segregation.
                                    </div>
                                    <div class="d-flex gap-1 flex-wrap">
                                        <span class="badge bg-success" title="Local occurrence images & ModelNetwork inventory">Data Feasibility</span>
                                        <span class="badge bg-info text-dark" title="Cumulative research agenda & previous findings">Program Agenda</span>
                                        <span class="badge bg-warning text-dark" title="WoRMS, bioRxiv & arXiv preprints">Domain & Literature</span>
                                    </div>
                                </div>
                            </div>

                            <!-- Promoted Project Elements Overview -->
                            <div class="card shadow-sm">
                                <div class="card-header bg-white fw-bold d-flex justify-content-between align-items-center">
                                    <span>Promoted Questions & Hypotheses</span>
                                    <span class="badge bg-secondary"><?= count($projectQuestions) ?> Qs</span>
                                </div>
                                <div class="card-body p-3 small">
                                    <?php if (empty($projectQuestions)): ?>
                                        <p class="text-muted mb-0">No questions promoted yet. Click <strong>Accept</strong> under any AI suggestion to promote it to the active project.</p>
                                    <?php else: ?>
                                        <ul class="list-unstyled mb-0">
                                            <?php foreach ($projectQuestions as $pq): ?>
                                                <li class="mb-2 pb-2 border-bottom">
                                                    <strong>Q<?= (int)$pq['id'] ?>:</strong> <?= h($pq['question']) ?>
                                                    <?php if (!empty($pq['source']) && $pq['source'] === 'brainstorming'): ?>
                                                        <div><span class="badge bg-info text-dark mt-1">Brainstorming #<?= (int)$pq['brainstorming_session_id'] ?></span></div>
                                                    <?php endif; ?>
                                                </li>
                                            <?php endforeach; ?>
                                        </ul>
                                    <?php endif; ?>
                                </div>
                            </div>
                        </div>

                        <!-- Active Session Details & Chat Workspace (Right Column) -->
                        <div class="col-lg-8">
                            <?php if ($selectedSession !== null): ?>
                                <div class="card shadow-sm mb-4">
                                    <div class="card-header bg-white py-3">
                                        <div class="d-flex justify-content-between align-items-start">
                                            <div>
                                                <span class="badge bg-light text-dark border me-2">Session #<?= (int)$selectedSession['id'] ?></span>
                                                <span class="badge <?= statusBadge($selectedSession['status']) ?>"><?= h($selectedSession['status']) ?></span>
                                                <h3 class="h5 mt-2 mb-1">Initial Research Idea</h3>
                                                <p class="text-muted mb-0"><?= h($selectedSession['initial_idea']) ?></p>
                                            </div>
                                            <!-- Action: Generate Research Plan -->
                                            <div class="d-flex gap-2">
                                                <form method="post" action="brainstorming.php?project_id=<?= $projectId ?>&session_id=<?= $selectedSessionId ?><?= $showArchived ? '&show_archived=1' : '' ?>" onsubmit="handleFormSubmit(this)">
                                                    <input type="hidden" name="action" value="generate_plan">
                                                    <input type="hidden" name="project_id" value="<?= $projectId ?>">
                                                    <input type="hidden" name="session_id" value="<?= $selectedSessionId ?>">
                                                    <button type="submit" class="btn btn-sm btn-success">
                                                        📋 Generate Research Plan
                                                    </button>
                                                </form>
                                                <!-- Status Update Dropdown -->
                                                <div class="dropdown">
                                                    <button class="btn btn-sm btn-outline-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown">
                                                        Manage
                                                    </button>
                                                    <ul class="dropdown-menu dropdown-menu-end">
                                                        <li>
                                                            <form method="post">
                                                                <input type="hidden" name="action" value="update_session">
                                                                <input type="hidden" name="project_id" value="<?= $projectId ?>">
                                                                <input type="hidden" name="session_id" value="<?= (int)$selectedSession['id'] ?>">
                                                                <input type="hidden" name="status" value="active">
                                                                <button type="submit" class="dropdown-item">Mark Active</button>
                                                            </form>
                                                        </li>
                                                        <li>
                                                            <form method="post">
                                                                <input type="hidden" name="action" value="update_session">
                                                                <input type="hidden" name="project_id" value="<?= $projectId ?>">
                                                                <input type="hidden" name="session_id" value="<?= (int)$selectedSession['id'] ?>">
                                                                <input type="hidden" name="status" value="completed">
                                                                <button type="submit" class="dropdown-item">Mark Completed</button>
                                                            </form>
                                                        </li>
                                                        <li><hr class="dropdown-divider"></li>
                                                        <?php if ($selectedSession['status'] === 'archived'): ?>
                                                            <li>
                                                                <form method="post">
                                                                    <input type="hidden" name="action" value="unarchive_session">
                                                                    <input type="hidden" name="project_id" value="<?= $projectId ?>">
                                                                    <input type="hidden" name="session_id" value="<?= (int)$selectedSession['id'] ?>">
                                                                    <button type="submit" class="dropdown-item text-success">Unarchive Session</button>
                                                                </form>
                                                            </li>
                                                        <?php else: ?>
                                                            <li>
                                                                <form method="post">
                                                                    <input type="hidden" name="action" value="archive_session">
                                                                    <input type="hidden" name="project_id" value="<?= $projectId ?>">
                                                                    <input type="hidden" name="session_id" value="<?= (int)$selectedSession['id'] ?>">
                                                                    <button type="submit" class="dropdown-item text-danger" onclick="return confirm('Archive/hide this session from the active list?');">Archive / Hide Session</button>
                                                                </form>
                                                            </li>
                                                        <?php endif; ?>
                                                    </ul>
                                                </div>
                                            </div>
                                        </div>


                                        <?php if (!empty($selectedSession['model_provenance'])): ?>
                                            <div class="mt-3 p-2 bg-light rounded small border">
                                                <strong>Model Provenance:</strong>
                                                Provider: <code><?= h($selectedSession['model_provenance']['provider'] ?? 'N/A') ?></code> |
                                                Model: <code><?= h($selectedSession['model_provenance']['model'] ?? 'N/A') ?></code>
                                                <?php if (isset($selectedSession['model_provenance']['latency_ms'])): ?>
                                                    | Latency: <?= (int)$selectedSession['model_provenance']['latency_ms'] ?> ms
                                                <?php endif; ?>
                                            </div>
                                        <?php endif; ?>

                                        <!-- Latest Research Plan Preview Card -->
                                        <?php if ($latestPlan !== null): ?>
                                            <div class="mt-3 p-3 bg-success-subtle border border-success rounded">
                                                <div class="d-flex justify-content-between align-items-center">
                                                    <div>
                                                        <strong class="text-success">Generated Research Plan (v<?= (int)$latestPlan['version'] ?>):</strong>
                                                        <div class="fw-bold"><?= h($latestPlan['title']) ?></div>
                                                        <div class="small text-muted">Status: <span class="badge bg-secondary"><?= h($latestPlan['status']) ?></span></div>
                                                    </div>
                                                    <div class="d-flex gap-1">
                                                        <button type="button" class="btn btn-xs btn-outline-primary" data-bs-toggle="modal" data-bs-target="#revisePlanModalSession">🔄 Revise</button>
                                                        <?php if ($latestPlan['status'] !== 'approved'): ?>
                                                            <form method="post" action="brainstorming.php?project_id=<?= $projectId ?>&session_id=<?= $selectedSessionId ?>">
                                                                <input type="hidden" name="action" value="approve_plan">
                                                                <input type="hidden" name="project_id" value="<?= $projectId ?>">
                                                                <input type="hidden" name="session_id" value="<?= $selectedSessionId ?>">
                                                                <input type="hidden" name="plan_id" value="<?= (int)$latestPlan['id'] ?>">
                                                                <button type="submit" class="btn btn-xs btn-success">✔ Approve</button>
                                                            </form>
                                                        <?php endif; ?>
                                                        <a href="research_plans.php?project_id=<?= $projectId ?>&plan_id=<?= (int)$latestPlan['id'] ?>" class="btn btn-xs btn-outline-secondary">View Full Plan →</a>
                                                    </div>
                                                </div>
                                            </div>

                                            <!-- Revise Plan Modal -->
                                            <div class="modal fade" id="revisePlanModalSession" tabindex="-1" aria-hidden="true">
                                                <div class="modal-dialog">
                                                    <div class="modal-content">
                                                        <form method="post" action="brainstorming.php?project_id=<?= $projectId ?>&session_id=<?= $selectedSessionId ?>" onsubmit="handleFormSubmit(this)">
                                                            <input type="hidden" name="action" value="revise_plan">
                                                            <input type="hidden" name="project_id" value="<?= $projectId ?>">
                                                            <input type="hidden" name="session_id" value="<?= $selectedSessionId ?>">
                                                            <input type="hidden" name="plan_id" value="<?= (int)$latestPlan['id'] ?>">

                                                            <div class="modal-header">
                                                                <h5 class="modal-title">Revise Research Plan (v<?= (int)$latestPlan['version'] + 1 ?>)</h5>
                                                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                                                            </div>
                                                            <div class="modal-body">
                                                                <div class="mb-3">
                                                                    <label class="form-label fw-semibold">Steering Instructions for AI</label>
                                                                    <textarea name="steering_instructions" class="form-control" rows="3" placeholder="e.g. Focus more strongly on taxonomy, reduce scope..." required></textarea>
                                                                </div>
                                                            </div>
                                                            <div class="modal-footer">
                                                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                                                <button type="submit" class="btn btn-primary">Generate Revision</button>
                                                            </div>
                                                        </form>
                                                    </div>
                                                </div>
                                            </div>
                                        <?php endif; ?>
                                    </div>

                                    <!-- Conversation Messages Timeline -->
                                    <div class="card-body p-4" style="max-height: 600px; overflow-y: auto;">
                                        <h4 class="h6 text-uppercase text-muted fw-semibold mb-3">Conversation History</h4>

                                        <?php
                                            $messages = $selectedSession['messages'] ?? [];
                                            $modalIndex = 0;

                                            // Build lookup map for accepted questions
                                            $acceptedQuestionMap = [];
                                            foreach ($projectQuestions as $pq) {
                                                $qClean = mb_strtolower(trim($pq['question'] ?? ''));
                                                if ($qClean !== '') {
                                                    $acceptedQuestionMap[$qClean] = (int)$pq['id'];
                                                }
                                            }

                                            // Build lookup map for accepted hypotheses
                                            $acceptedHypothesisMap = [];
                                            foreach ($projectHypotheses as $ph) {
                                                $hClean = mb_strtolower(trim($ph['statement'] ?? ''));
                                                if ($hClean !== '') {
                                                    $acceptedHypothesisMap[$hClean] = (int)$ph['id'];
                                                }
                                            }

                                            // Build lookup map for rejected candidate texts
                                            $rejectedCandidateTexts = [];
                                            foreach ($messages as $m) {
                                                $mc = $m['content'] ?? '';
                                                if (stripos($mc, 'Rejected Candidate') !== false) {
                                                    if (preg_match('/Rejected Candidate \([^)]+\):\s*"([^"]+)"/i', $mc, $matches)) {
                                                        $rejectedCandidateTexts[mb_strtolower(trim($matches[1]))] = true;
                                                    }
                                                }
                                            }
                                        ?>
                                        <?php if (empty($messages)): ?>
                                            <p class="text-muted italic">No messages in this session yet.</p>
                                        <?php else: ?>
                                            <?php foreach ($messages as $msgIdx => $msg): ?>
                                                <?php
                                                    $role = strtolower($msg['role'] ?? 'user');
                                                    $bubbleClass = 'chat-bubble-user';
                                                    $roleTitle = 'Researcher';
                                                    if ($role === 'assistant' || $role === 'ai_scientist') {
                                                        $bubbleClass = 'chat-bubble-assistant';
                                                        $roleTitle = 'AI Scientist';
                                                    } elseif ($role === 'system') {
                                                        $bubbleClass = 'chat-bubble-system';
                                                        $roleTitle = 'System Note';
                                                    }

                                                    $candidates = ($role === 'assistant' || $role === 'ai_scientist')
                                                        ? extractCandidatesFromText($msg['content'] ?? '')
                                                        : ['questions' => [], 'hypotheses' => []];
                                                ?>
                                                <div class="p-3 mb-3 rounded shadow-sm <?= $bubbleClass ?>">
                                                    <div class="d-flex justify-content-between align-items-center mb-1">
                                                        <strong class="small"><?= h($roleTitle) ?></strong>
                                                        <?php if (!empty($msg['timestamp'])): ?>
                                                            <span class="small text-muted"><?= h($msg['timestamp']) ?></span>
                                                        <?php endif; ?>
                                                    </div>
                                                    <div style="white-space: pre-wrap;"><?= h($msg['content']) ?></div>

                                                    <!-- Inline Promotion Panel for AI Scientist Messages -->
                                                    <?php if (!empty($candidates['questions']) || !empty($candidates['hypotheses'])): ?>
                                                        <div class="mt-3 pt-3 border-top bg-white p-3 rounded">
                                                            <div class="small fw-bold text-primary mb-2">
                                                                <i class="bi bi-stars me-1"></i>Suggested Items & Actions ("Brainstorm freely; promote selectively")
                                                            </div>

                                                            <!-- Questions -->
                                                            <?php foreach ($candidates['questions'] as $sqText): ?>
                                                                <?php 
                                                                    $modalIndex++; 
                                                                    $cleanSq = mb_strtolower(trim($sqText));
                                                                    $isAcceptedQ = false;
                                                                    $acceptedQId = 0;
                                                                    foreach ($acceptedQuestionMap as $k => $v) {
                                                                        if ($k === $cleanSq || (strlen($cleanSq) > 15 && (strpos($k, $cleanSq) !== false || strpos($cleanSq, $k) !== false))) {
                                                                            $isAcceptedQ = true;
                                                                            $acceptedQId = $v;
                                                                            break;
                                                                        }
                                                                    }
                                                                    $isRejectedQ = false;
                                                                    foreach ($rejectedCandidateTexts as $rk => $rv) {
                                                                        if ($rk === $cleanSq || (strlen($cleanSq) > 15 && (strpos($rk, $cleanSq) !== false || strpos($cleanSq, $rk) !== false))) {
                                                                            $isRejectedQ = true;
                                                                            break;
                                                                        }
                                                                    }
                                                                ?>
                                                                <div class="p-2 mb-2 bg-light rounded border">
                                                                    <div class="small fw-semibold text-dark mb-1">Suggested Question: <?= h($sqText) ?></div>
                                                                    <div class="d-flex flex-wrap gap-2 align-items-center">
                                                                        <?php if ($isAcceptedQ): ?>
                                                                            <span class="badge bg-success py-1 px-2">
                                                                                <i class="bi bi-check-circle-fill me-1"></i>Accepted as Canonical Question Q<?= $acceptedQId ?>
                                                                            </span>
                                                                            <a href="questions.php?project_id=<?= $projectId ?>" class="btn btn-xs btn-outline-success py-0 px-2" style="font-size: 0.75rem;">
                                                                                View in Questions &rarr;
                                                                            </a>
                                                                        <?php elseif ($isRejectedQ): ?>
                                                                            <span class="badge bg-danger py-1 px-2">
                                                                                <i class="bi bi-x-circle-fill me-1"></i>Rejected (Audit Logged)
                                                                            </span>
                                                                        <?php else: ?>
                                                                            <form method="post" action="brainstorming.php?project_id=<?= $projectId ?>&session_id=<?= $selectedSessionId ?>" class="d-inline">
                                                                                <input type="hidden" name="action" value="promote_question">
                                                                                <input type="hidden" name="project_id" value="<?= $projectId ?>">
                                                                                <input type="hidden" name="session_id" value="<?= $selectedSessionId ?>">
                                                                                <input type="hidden" name="question" value="<?= h($sqText) ?>">
                                                                                <button type="submit" class="btn btn-xs btn-success py-0 px-2" style="font-size: 0.75rem;">✔ Accept</button>
                                                                            </form>
                                                                            <button type="button" class="btn btn-xs btn-outline-primary py-0 px-2" style="font-size: 0.75rem;" data-bs-toggle="modal" data-bs-target="#editQModal<?= $modalIndex ?>">✏ Edit & Accept</button>
                                                                            <button type="button" class="btn btn-xs btn-outline-danger py-0 px-2" style="font-size: 0.75rem;" data-bs-toggle="modal" data-bs-target="#rejectQModal<?= $modalIndex ?>">✖ Reject</button>
                                                                            <span class="badge bg-white text-muted border" style="font-size: 0.7rem;">Keep in Plan only</span>
                                                                        <?php endif; ?>
                                                                    </div>
                                                                </div>

                                                                <!-- Edit Q Modal -->
                                                                <div class="modal fade" id="editQModal<?= $modalIndex ?>" tabindex="-1" aria-hidden="true">
                                                                    <div class="modal-dialog">
                                                                        <div class="modal-content text-start">
                                                                            <form method="post" action="brainstorming.php?project_id=<?= $projectId ?>&session_id=<?= $selectedSessionId ?>">
                                                                                <input type="hidden" name="action" value="promote_question">
                                                                                <input type="hidden" name="project_id" value="<?= $projectId ?>">
                                                                                <input type="hidden" name="session_id" value="<?= $selectedSessionId ?>">

                                                                                <div class="modal-header">
                                                                                    <h5 class="modal-title">Edit & Accept Research Question</h5>
                                                                                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                                                                                </div>
                                                                                <div class="modal-body">
                                                                                    <div class="mb-3">
                                                                                        <label class="form-label fw-semibold">Research Question Text</label>
                                                                                        <textarea name="question" class="form-control" rows="3" required><?= h($sqText) ?></textarea>
                                                                                    </div>
                                                                                    <div class="mb-3">
                                                                                        <label class="form-label small">Inferential Level (optional)</label>
                                                                                        <input type="text" name="inferential_level" class="form-control form-control-sm" placeholder="e.g. population, species, morphometric">
                                                                                    </div>
                                                                                </div>
                                                                                <div class="modal-footer">
                                                                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                                                                    <button type="submit" class="btn btn-success">Save & Promote</button>
                                                                                </div>
                                                                            </form>
                                                                        </div>
                                                                    </div>
                                                                </div>

                                                                <!-- Reject Q Modal -->
                                                                <div class="modal fade" id="rejectQModal<?= $modalIndex ?>" tabindex="-1" aria-hidden="true">
                                                                    <div class="modal-dialog">
                                                                        <div class="modal-content text-start">
                                                                            <form method="post" action="brainstorming.php?project_id=<?= $projectId ?>&session_id=<?= $selectedSessionId ?>">
                                                                                <input type="hidden" name="action" value="reject_candidate">
                                                                                <input type="hidden" name="project_id" value="<?= $projectId ?>">
                                                                                <input type="hidden" name="session_id" value="<?= $selectedSessionId ?>">
                                                                                <input type="hidden" name="candidate_type" value="question">
                                                                                <input type="hidden" name="candidate_text" value="<?= h($sqText) ?>">

                                                                                <div class="modal-header">
                                                                                    <h5 class="modal-title">Reject Candidate Question</h5>
                                                                                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                                                                                </div>
                                                                                <div class="modal-body">
                                                                                    <p class="small text-muted">Rejecting records the audit reason in conversation history without creating a project question.</p>
                                                                                    <div class="mb-3">
                                                                                        <label class="form-label fw-semibold">Rejection Rationale (optional)</label>
                                                                                        <textarea name="reason" class="form-control" rows="2" placeholder="e.g. Out of scope for current dataset boundaries"></textarea>
                                                                                    </div>
                                                                                </div>
                                                                                <div class="modal-footer">
                                                                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                                                                    <button type="submit" class="btn btn-danger">Confirm Rejection</button>
                                                                                </div>
                                                                            </form>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            <?php endforeach; ?>

                                                            <!-- Hypotheses -->
                                                            <?php foreach ($candidates['hypotheses'] as $shText): ?>
                                                                <?php 
                                                                    $modalIndex++; 
                                                                    $cleanSh = mb_strtolower(trim($shText));
                                                                    $isAcceptedH = false;
                                                                    $acceptedHId = 0;
                                                                    foreach ($acceptedHypothesisMap as $k => $v) {
                                                                        if ($k === $cleanSh || (strlen($cleanSh) > 15 && (strpos($k, $cleanSh) !== false || strpos($cleanSh, $k) !== false))) {
                                                                            $isAcceptedH = true;
                                                                            $acceptedHId = $v;
                                                                            break;
                                                                        }
                                                                    }
                                                                    $isRejectedH = false;
                                                                    foreach ($rejectedCandidateTexts as $rk => $rv) {
                                                                        if ($rk === $cleanSh || (strlen($cleanSh) > 15 && (strpos($rk, $cleanSh) !== false || strpos($cleanSh, $rk) !== false))) {
                                                                            $isRejectedH = true;
                                                                            break;
                                                                        }
                                                                    }
                                                                ?>
                                                                <div class="p-2 mb-2 bg-light rounded border">
                                                                    <div class="small fw-semibold text-dark mb-1">Candidate Hypothesis: <?= h($shText) ?></div>
                                                                    <?php if ($isAcceptedH): ?>
                                                                        <div class="d-flex gap-2 align-items-center">
                                                                            <span class="badge bg-success py-1 px-2">
                                                                                <i class="bi bi-check-circle-fill me-1"></i>Accepted as Canonical Hypothesis H<?= $acceptedHId ?>
                                                                            </span>
                                                                            <a href="hypotheses.php?project_id=<?= $projectId ?>" class="btn btn-xs btn-outline-success py-0 px-2" style="font-size: 0.75rem;">
                                                                                View in Hypotheses &rarr;
                                                                            </a>
                                                                        </div>
                                                                    <?php elseif ($isRejectedH): ?>
                                                                        <span class="badge bg-danger py-1 px-2">
                                                                            <i class="bi bi-x-circle-fill me-1"></i>Rejected (Audit Logged)
                                                                        </span>
                                                                    <?php elseif (empty($projectQuestions)): ?>
                                                                        <div class="small text-danger">Please accept a Research Question above first to link this hypothesis.</div>
                                                                    <?php else: ?>
                                                                        <form method="post" action="brainstorming.php?project_id=<?= $projectId ?>&session_id=<?= $selectedSessionId ?>" class="row g-1 align-items-center">
                                                                            <input type="hidden" name="action" value="promote_hypothesis">
                                                                            <input type="hidden" name="project_id" value="<?= $projectId ?>">
                                                                            <input type="hidden" name="session_id" value="<?= $selectedSessionId ?>">
                                                                            <input type="hidden" name="statement" value="<?= h($shText) ?>">

                                                                            <div class="col-sm-6">
                                                                                <select name="question_id" class="form-select form-select-sm py-0" style="font-size: 0.75rem;" required>
                                                                                    <option value="">-- Target Research Question --</option>
                                                                                    <?php foreach ($projectQuestions as $pq): ?>
                                                                                        <option value="<?= (int)$pq['id'] ?>">Q<?= (int)$pq['id'] ?>: <?= h(mb_strimwidth($pq['question'], 0, 45, '...')) ?></option>
                                                                                    <?php endforeach; ?>
                                                                                </select>
                                                                            </div>
                                                                            <div class="col-sm-6 d-flex gap-1">
                                                                                <button type="submit" class="btn btn-xs btn-success py-0 px-2" style="font-size: 0.75rem;">✔ Accept</button>
                                                                                <button type="button" class="btn btn-xs btn-outline-primary py-0 px-2" style="font-size: 0.75rem;" data-bs-toggle="modal" data-bs-target="#editHModal<?= $modalIndex ?>">✏ Edit</button>
                                                                                <button type="button" class="btn btn-xs btn-outline-danger py-0 px-2" style="font-size: 0.75rem;" data-bs-toggle="modal" data-bs-target="#rejectHModal<?= $modalIndex ?>">✖ Reject</button>
                                                                            </div>
                                                                        </form>
                                                                    <?php endif; ?>
                                                                </div>


                                                                <!-- Edit H Modal -->
                                                                <div class="modal fade" id="editHModal<?= $modalIndex ?>" tabindex="-1" aria-hidden="true">
                                                                    <div class="modal-dialog">
                                                                        <div class="modal-content text-start">
                                                                            <form method="post" action="brainstorming.php?project_id=<?= $projectId ?>&session_id=<?= $selectedSessionId ?>">
                                                                                <input type="hidden" name="action" value="promote_hypothesis">
                                                                                <input type="hidden" name="project_id" value="<?= $projectId ?>">
                                                                                <input type="hidden" name="session_id" value="<?= $selectedSessionId ?>">

                                                                                <div class="modal-header">
                                                                                    <h5 class="modal-title">Edit & Accept Hypothesis</h5>
                                                                                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                                                                                </div>
                                                                                <div class="modal-body">
                                                                                    <div class="mb-3">
                                                                                        <label class="form-label fw-semibold">Target Research Question</label>
                                                                                        <select name="question_id" class="form-select form-select-sm" required>
                                                                                            <option value="">-- Select Parent Research Question --</option>
                                                                                            <?php foreach ($projectQuestions as $pq): ?>
                                                                                                <option value="<?= (int)$pq['id'] ?>">Q<?= (int)$pq['id'] ?>: <?= h($pq['question']) ?></option>
                                                                                            <?php endforeach; ?>
                                                                                        </select>
                                                                                    </div>
                                                                                    <div class="mb-3">
                                                                                        <label class="form-label fw-semibold">Hypothesis Statement</label>
                                                                                        <textarea name="statement" class="form-control" rows="3" required><?= h($shText) ?></textarea>
                                                                                    </div>
                                                                                    <div class="mb-3">
                                                                                        <label class="form-label small">Scientific Rationale (optional)</label>
                                                                                        <textarea name="rationale" class="form-control form-control-sm" rows="2" placeholder="Theoretical or empirical rationale..."></textarea>
                                                                                    </div>
                                                                                </div>
                                                                                <div class="modal-footer">
                                                                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                                                                    <button type="submit" class="btn btn-success">Save & Promote</button>
                                                                                </div>
                                                                            </form>
                                                                        </div>
                                                                    </div>
                                                                </div>

                                                                <!-- Reject H Modal -->
                                                                <div class="modal fade" id="rejectHModal<?= $modalIndex ?>" tabindex="-1" aria-hidden="true">
                                                                    <div class="modal-dialog">
                                                                        <div class="modal-content text-start">
                                                                            <form method="post" action="brainstorming.php?project_id=<?= $projectId ?>&session_id=<?= $selectedSessionId ?>">
                                                                                <input type="hidden" name="action" value="reject_candidate">
                                                                                <input type="hidden" name="project_id" value="<?= $projectId ?>">
                                                                                <input type="hidden" name="session_id" value="<?= $selectedSessionId ?>">
                                                                                <input type="hidden" name="candidate_type" value="hypothesis">
                                                                                <input type="hidden" name="candidate_text" value="<?= h($shText) ?>">

                                                                                <div class="modal-header">
                                                                                    <h5 class="modal-title">Reject Candidate Hypothesis</h5>
                                                                                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                                                                                </div>
                                                                                <div class="modal-body">
                                                                                    <div class="mb-3">
                                                                                        <label class="form-label fw-semibold">Rejection Rationale (optional)</label>
                                                                                        <textarea name="reason" class="form-control" rows="2" placeholder="e.g. Assumes discrete forms before testing continuity"></textarea>
                                                                                    </div>
                                                                                </div>
                                                                                <div class="modal-footer">
                                                                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                                                                    <button type="submit" class="btn btn-danger">Confirm Rejection</button>
                                                                                </div>
                                                                            </form>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            <?php endforeach; ?>
                                                        </div>
                                                    <?php endif; ?>
                                                </div>
                                            <?php endforeach; ?>
                                        <?php endif; ?>
                                    </div>

                                    <!-- Chat Reply Form -->
                                    <div class="card-footer bg-white p-3">
                                        <form method="post" action="brainstorming.php?project_id=<?= $projectId ?>&session_id=<?= (int)$selectedSession['id'] ?>" onsubmit="handleFormSubmit(this)">
                                            <input type="hidden" name="action" value="add_message">
                                            <input type="hidden" name="project_id" value="<?= $projectId ?>">
                                            <input type="hidden" name="session_id" value="<?= (int)$selectedSession['id'] ?>">

                                            <div class="mb-2">
                                                <label class="form-label small fw-semibold">Add Follow-up Message / Steering</label>
                                                <div class="row g-2">
                                                    <div class="col-sm-3">
                                                        <select name="role" class="form-select form-select-sm">
                                                            <option value="user">Researcher (User)</option>
                                                            <option value="assistant">AI Scientist (Assistant)</option>
                                                            <option value="system">System Note</option>
                                                        </select>
                                                    </div>
                                                    <div class="col-sm-9">
                                                        <textarea name="content" class="form-control" rows="3" placeholder="Type message or steering instruction..." required><?= h($lastContent) ?></textarea>
                                                    </div>
                                                </div>
                                            </div>
                                            <div class="d-flex justify-content-between align-items-center">
                                                <button type="submit" class="btn btn-primary" id="btnSendMessage">
                                                    Send Message
                                                </button>
                                            </div>
                                        </form>
                                    </div>
                                </div>
                            <?php endif; ?>
                        </div>
                    </div>

                <?php endif; ?>

            </main>
        </div>
    </div>

    <!-- New Session Modal -->
    <div class="modal fade" id="newSessionModal" tabindex="-1" aria-labelledby="newSessionModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <form method="post" action="brainstorming.php?project_id=<?= $projectId ?>" onsubmit="handleFormSubmit(this)">
                    <input type="hidden" name="action" value="create_session">
                    <input type="hidden" name="project_id" value="<?= $projectId ?>">

                    <div class="modal-header">
                        <h5 class="modal-title" id="newSessionModalLabel">Start New Brainstorming Session</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <label class="form-label fw-semibold">Initial Research Idea / Objective</label>
                            <textarea name="initial_idea" class="form-control" rows="4" placeholder="Describe the biological phenomenon, question, or dataset hypothesis you would like to explore..." required><?= h($lastInitialIdea) ?></textarea>
                            <div class="form-text">This will create a new persistent session attached to Research Project #<?= (int)$project['id'] ?>.</div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="submit" class="btn btn-primary">Create Session</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

<?php endif; ?>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js"></script>
<script>
function handleFormSubmit(form) {
    const btn = form.querySelector('button[type="submit"]');
    if (!btn) return;
    btn.classList.add('disabled');
    btn.setAttribute('disabled', 'disabled');
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Querying AI Scientist...';
}
</script>

<!-- Compare Taxa Modal -->
<div class="modal fade" id="compareTaxaModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title font-monospace fw-bold">Tri-Criterion Taxon Prioritization</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <p class="text-muted small mb-3">
                    Compare two candidate genera across <strong>Data Feasibility</strong> (DWH image counts), <strong>Research Program Value</strong> (agenda questions), and <strong>Domain Intelligence</strong> (WoRMS taxonomy, cryptic diversity, preprints).
                </p>
                <div class="row g-3 mb-3">
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Candidate Taxon A</label>
                        <input type="text" id="cmpTaxonA" class="form-control form-control-sm font-monospace" value="Nassarius" placeholder="e.g. Nassarius">
                    </div>
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Candidate Taxon B</label>
                        <input type="text" id="cmpTaxonB" class="form-control form-control-sm font-monospace" value="Vexillum" placeholder="e.g. Vexillum">
                    </div>
                </div>
                <div class="d-grid mb-3">
                    <button type="button" class="btn btn-sm btn-primary" onclick="runTaxaComparison()">
                        Run Tri-Grounded Prioritization
                    </button>
                </div>
                <div id="cmpResults" class="p-3 bg-light rounded border small d-none">
                    <h6 class="fw-bold text-dark font-monospace mb-2" id="cmpWinnerTitle"></h6>
                    <p id="cmpJustification" class="text-secondary mb-3"></p>
                    <div class="row g-2" id="cmpDetails"></div>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-sm btn-secondary" data-bs-dismiss="modal">Close</button>
            </div>
        </div>
    </div>
</div>

<script>
async function runTaxaComparison() {
    const a = document.getElementById('cmpTaxonA').value.trim();
    const b = document.getElementById('cmpTaxonB').value.trim();
    const resBox = document.getElementById('cmpResults');
    if (!a || !b) return;

    resBox.classList.remove('d-none');
    resBox.innerHTML = '<div class="text-center py-3 text-muted"><div class="spinner-border spinner-border-sm text-primary me-2"></div> Querying DWH, WoRMS, and preprints...</div>';

    try {
        const resp = await fetch('ajax_api.php?action=compare_taxa', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ taxon_a: a, taxon_b: b })
        });
        if (!resp.ok) throw new Error('Comparison API returned ' + resp.status);
        const data = await resp.json();

        resBox.innerHTML = `
            <div class="alert alert-success py-2 mb-3">
                <strong>Recommended Priority:</strong> ${data.recommended_priority}
            </div>
            <p class="mb-3">${data.justification}</p>
            <div class="row g-2 font-monospace small">
                <div class="col-6">
                    <div class="p-2 border rounded bg-white">
                        <strong>${data.taxon_a}:</strong><br>
                        - Images in DWH: ${data.taxon_a_summary.data_feasibility.total_images || 0}<br>
                        - Cryptic Complexes: ${data.taxon_a_summary.domain_context.has_cryptic_complexes ? 'Yes' : 'No'}<br>
                        - WoRMS Status: ${(data.taxon_a_summary.domain_context.worms?.status || 'N/A').toUpperCase()}
                    </div>
                </div>
                <div class="col-6">
                    <div class="p-2 border rounded bg-white">
                        <strong>${data.taxon_b}:</strong><br>
                        - Images in DWH: ${data.taxon_b_summary.data_feasibility.total_images || 0}<br>
                        - Cryptic Complexes: ${data.taxon_b_summary.domain_context.has_cryptic_complexes ? 'Yes' : 'No'}<br>
                        - WoRMS Status: ${(data.taxon_b_summary.domain_context.worms?.status || 'N/A').toUpperCase()}
                    </div>
                </div>
            </div>
        `;
    } catch (err) {
        resBox.innerHTML = `<div class="alert alert-danger py-2 mb-0">Error: ${err.message}</div>`;
    }
}
</script>


<!-- Inspect Orchestrator Modal -->
<div class="modal fade" id="inspectOrchestratorModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-xl">
        <div class="modal-content">
            <div class="modal-header bg-dark text-white">
                <h5 class="modal-title font-monospace">Adaptive Research Intelligence Orchestrator</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <p class="text-muted small mb-3">
                    Test the dynamic routing and view the assembled <strong>ResearchIntelligencePacket</strong> and prompt injection payload for any scientific question in real time.
                </p>
                <div class="input-group mb-3">
                    <input type="text" id="orchQueryInput" class="form-control font-monospace" placeholder="e.g. Which feasible taxon has the strongest biological research value and cryptic diversity?" value="Which feasible taxon has the strongest biological research value and cryptic diversity?">
                    <button class="btn btn-primary" type="button" onclick="runOrchestratorInspection()">
                        Route & Inspect Packet
                    </button>
                </div>
                <div id="orchInspectionResult" class="p-3 bg-light rounded border font-monospace small d-none" style="max-height: 500px; overflow-y: auto;">
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-sm btn-secondary" data-bs-dismiss="modal">Close</button>
            </div>
        </div>
    </div>
</div>

<script>
async function runOrchestratorInspection() {
    const q = document.getElementById('orchQueryInput').value.trim();
    const resBox = document.getElementById('orchInspectionResult');
    if (!q) return;

    resBox.classList.remove('d-none');
    resBox.innerHTML = '<div class="text-center py-3 text-muted"><div class="spinner-border spinner-border-sm text-primary me-2"></div> Assembling ResearchIntelligencePacket across active layers...</div>';

    try {
        const resp = await fetch('ajax_api.php?action=inspect_packet', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: q, project_id: <?= (int)$projectId ?> })
        });
        if (!resp.ok) throw new Error('Orchestrator returned ' + resp.status);
        const data = await resp.json();

        const act = data.packet.retrieval_summary.activated_layers || [];
        const skip = data.packet.retrieval_summary.skipped_layers || [];
        const lat = data.packet.retrieval_summary.latency_ms || 0;
        const rat = data.packet.retrieval_summary.routing_rationale || '';

        let badges = act.map(l => `<span class="badge bg-success me-1">${l}</span>`).join(' ');
        let skipBadges = skip.map(l => `<span class="badge bg-secondary me-1">${l}</span>`).join(' ');

        resBox.innerHTML = `
            <div class="alert alert-info py-2 mb-3">
                <strong>Routing Decision:</strong> ${rat}<br>
                <div class="mt-1"><strong>Activated:</strong> ${badges || 'None (Context only)'}</div>
                <div class="mt-1"><strong>Skipped:</strong> ${skipBadges || 'None'}</div>
                <div class="mt-1 text-muted small"><strong>Retrieval Latency:</strong> ${lat} ms</div>
            </div>
            <h6 class="fw-bold text-dark mb-2">Assembled ResearchIntelligencePacket:</h6>
            <pre class="bg-white p-3 border rounded text-dark" style="white-space: pre-wrap; font-size: 11px;">${data.formatted_prompt}</pre>
        `;
    } catch (err) {
        resBox.innerHTML = `<div class="alert alert-danger py-2 mb-0">Error: ${err.message}</div>`;
    }
}
</script>

</body>
</html>
