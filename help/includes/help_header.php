<?php

declare(strict_types=1);

if (!isset($pageTitle)) {
    $pageTitle = 'Help & Documentation — Biodiversity AI Scientist';
}

$projectId = isset($_GET['project_id']) && is_numeric($_GET['project_id']) && (int)$_GET['project_id'] > 0
    ? (int)$_GET['project_id']
    : (isset($projectId) && is_numeric($projectId) && (int)$projectId > 0 ? (int)$projectId : null);

$projParam = $projectId ? '?project_id=' . $projectId : '';
$activeTopic = $activeTopic ?? '';

$topics = [
    'index' => [
        'title' => 'Help Index',
        'file' => 'index.php',
        'icon' => 'bi-grid-fill',
        'category' => 'Home'
    ],
    'architecture' => [
        'title' => 'System Architecture',
        'file' => 'architecture.php',
        'icon' => 'bi-diagram-3-fill',
        'category' => 'Foundations'
    ],
    'user_manual' => [
        'title' => 'End-to-End User Manual',
        'file' => 'user_manual.php',
        'icon' => 'bi-book-fill',
        'category' => 'Foundations'
    ],
    'brainstorming' => [
        'title' => 'Brainstorming & Ideation',
        'file' => 'brainstorming.php',
        'icon' => 'bi-lightbulb-fill',
        'category' => 'Discovery'
    ],
    'research_plans' => [
        'title' => 'Phase 6: Research Plans',
        'file' => 'research_plans.php',
        'icon' => 'bi-file-earmark-text-fill',
        'category' => 'Discovery'
    ],
    'scientific_context' => [
        'title' => 'Phase 7: Scientific Context Engine',
        'file' => 'scientific_context.php',
        'icon' => 'bi-intersect',
        'category' => 'Discovery'
    ],
    'investigation_planning' => [
        'title' => 'Phase 8: Investigation DAGs',
        'file' => 'investigation_planning.php',
        'icon' => 'bi-diagram-2-fill',
        'category' => 'Sequencing'
    ],
    'capabilities' => [
        'title' => 'Phase 9: Capability Registry',
        'file' => 'capabilities.php',
        'icon' => 'bi-tools',
        'category' => 'Sequencing'
    ],
    'analyses' => [
        'title' => 'Phase 10: Empirical Analyses',
        'file' => 'analyses.php',
        'icon' => 'bi-flask-fill',
        'category' => 'Sequencing'
    ],
    'faq' => [
        'title' => 'FAQ & Troubleshooting',
        'file' => 'faq.php',
        'icon' => 'bi-question-circle-fill',
        'category' => 'Reference'
    ],
    'technical_reference' => [
        'title' => 'Technical Reference (DB & APIs)',
        'file' => 'technical_reference.php',
        'icon' => 'bi-code-square',
        'category' => 'Reference'
    ],
];

?>
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title><?= htmlspecialchars($pageTitle, ENT_QUOTES, 'UTF-8') ?></title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
    <link href="/ai-scientist/css/app.css" rel="stylesheet">
    <style>
        .help-hero {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0d6efd 100%);
            color: #ffffff;
            border-radius: 0.75rem;
            padding: 3rem 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
        }
        .help-card {
            transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.2s cubic-bezier(0.16, 1, 0.3, 1);
            cursor: pointer;
            height: 100%;
            border-radius: 0.75rem;
            border: 1px solid #e2e8f0;
            background: #ffffff;
        }
        .help-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 24px rgba(13, 110, 253, 0.12);
            border-color: #93c5fd;
        }
        .help-icon-circle {
            width: 52px;
            height: 52px;
            border-radius: 12px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            margin-bottom: 1rem;
        }
        .code-snippet {
            background-color: #0f172a;
            color: #f8fafc;
            padding: 1.1rem 1.25rem;
            border-radius: 8px;
            font-family: "SFMono-Regular", Menlo, Monaco, Consolas, monospace;
            font-size: 0.88rem;
            overflow-x: auto;
            border: 1px solid #1e293b;
        }
        .svg-container {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.03);
            text-align: center;
            overflow-x: auto;
        }
        .spec-table th {
            background-color: #f1f5f9;
            color: #334155;
            font-weight: 600;
        }
        .sidebar-help-link {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 0.75rem;
            border-radius: 6px;
            color: #475569;
            text-decoration: none;
            font-size: 0.9rem;
            transition: background-color 0.15s, color 0.15s;
        }
        .sidebar-help-link:hover {
            background-color: #e2e8f0;
            color: #0f172a;
        }
        .sidebar-help-link.active {
            background-color: #0d6efd;
            color: #ffffff;
            font-weight: 600;
        }
    </style>
</head>
<body class="bg-light text-dark">

<nav class="navbar navbar-expand-lg navbar-dark bg-dark sticky-top shadow-sm">
    <div class="container-fluid">
        <a class="navbar-brand d-flex align-items-center fw-bold" href="/ai-scientist/help/index.php<?= $projParam ?>">
            <i class="bi bi-book-half text-primary me-2"></i>
            <span>AI Scientist Documentation</span>
        </a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#helpNavbar" aria-controls="helpNavbar" aria-expanded="false" aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
        </button>
        
        <div class="collapse navbar-collapse" id="helpNavbar">
            <ul class="navbar-nav me-auto mb-2 mb-lg-0">
                <li class="nav-item">
                    <a class="nav-link <?= $activeTopic === 'index' ? 'active fw-semibold' : '' ?>" href="index.php<?= $projParam ?>">
                        <i class="bi bi-house-door me-1"></i>Help Index
                    </a>
                </li>
                <li class="nav-item dropdown">
                    <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                        <i class="bi bi-list-nested me-1"></i>Topics
                    </a>
                    <ul class="dropdown-menu shadow">
                        <li><h6 class="dropdown-header">Foundations</h6></li>
                        <li><a class="dropdown-item" href="architecture.php<?= $projParam ?>"><i class="bi bi-diagram-3 me-2 text-primary"></i>System Architecture</a></li>
                        <li><a class="dropdown-item" href="user_manual.php<?= $projParam ?>"><i class="bi bi-book me-2 text-primary"></i>End-to-End User Manual</a></li>
                        <li><hr class="dropdown-divider"></li>
                        <li><h6 class="dropdown-header">Discovery & Planning</h6></li>
                        <li><a class="dropdown-item" href="brainstorming.php<?= $projParam ?>"><i class="bi bi-lightbulb me-2 text-warning"></i>Brainstorming & Ideation</a></li>
                        <li><a class="dropdown-item" href="research_plans.php<?= $projParam ?>"><i class="bi bi-file-earmark-text me-2 text-info"></i>Research Plans (Phase 6)</a></li>
                        <li><a class="dropdown-item" href="scientific_context.php<?= $projParam ?>"><i class="bi bi-intersect me-2 text-success"></i>Context Engine (Phase 7)</a></li>
                        <li><hr class="dropdown-divider"></li>
                        <li><h6 class="dropdown-header">Sequencing & Execution</h6></li>
                        <li><a class="dropdown-item" href="investigation_planning.php<?= $projParam ?>"><i class="bi bi-diagram-2 me-2 text-primary"></i>Investigation DAGs (Phase 8)</a></li>
                        <li><a class="dropdown-item" href="capabilities.php<?= $projParam ?>"><i class="bi bi-tools me-2 text-secondary"></i>Capabilities & Tools (Phase 9)</a></li>
                        <li><a class="dropdown-item" href="analyses.php<?= $projParam ?>"><i class="bi bi-flask me-2 text-danger"></i>Empirical Analyses (Phase 10)</a></li>
                        <li><hr class="dropdown-divider"></li>
                        <li><h6 class="dropdown-header">Reference</h6></li>
                        <li><a class="dropdown-item" href="faq.php<?= $projParam ?>"><i class="bi bi-question-circle me-2 text-muted"></i>FAQ & Troubleshooting</a></li>
                        <li><a class="dropdown-item" href="technical_reference.php<?= $projParam ?>"><i class="bi bi-code-square me-2 text-dark"></i>Technical Reference</a></li>
                    </ul>
                </li>
            </ul>

            <div class="d-flex align-items-center gap-2">
                <?php if ($projectId): ?>
                    <a href="/ai-scientist/project.php?project_id=<?= $projectId ?>" class="btn btn-sm btn-outline-light">
                        <i class="bi bi-arrow-left me-1"></i>Back to Project #<?= $projectId ?>
                    </a>
                <?php else: ?>
                    <a href="/ai-scientist/projects.php" class="btn btn-sm btn-outline-light">
                        <i class="bi bi-arrow-left me-1"></i>Back to Workspace
                    </a>
                <?php endif; ?>
            </div>
        </div>
    </div>
</nav>

<div class="container-fluid py-4 px-lg-5">
    <!-- Breadcrumbs -->
    <nav aria-label="breadcrumb" class="mb-3">
        <ol class="breadcrumb bg-white p-2 px-3 rounded shadow-sm border small">
            <li class="breadcrumb-item"><a href="/ai-scientist/projects.php" class="text-decoration-none"><i class="bi bi-grid me-1"></i>Workspace</a></li>
            <li class="breadcrumb-item"><a href="index.php<?= $projParam ?>" class="text-decoration-none">Help Center</a></li>
            <?php if ($activeTopic !== 'index' && isset($topics[$activeTopic])): ?>
                <li class="breadcrumb-item active text-dark fw-semibold" aria-current="page"><?= htmlspecialchars($topics[$activeTopic]['title'], ENT_QUOTES, 'UTF-8') ?></li>
            <?php endif; ?>
        </ol>
    </nav>
