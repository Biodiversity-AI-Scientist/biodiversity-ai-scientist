<?php

declare(strict_types=1);

$currentScript = basename($_SERVER['SCRIPT_NAME'] ?? '');
$currentProjectId = isset($projectId) && (int)$projectId > 0 ? (int)$projectId : (int)($_GET['project_id'] ?? 0);
$projParam = $currentProjectId > 0 ? '?project_id=' . $currentProjectId : '';

$isProjectsActive = in_array(
    $currentScript,
    [
        'projects.php',
        'project.php',
        'brainstorming.php',
        'brainstorming_help.php',
        'research_plans.php',
        'investigation_plan.php',
        'questions.php',
        'hypotheses.php',
        'dataset.php',
        'analyses.php',
        'analyses_help.php',
    ],
    true
);
$isAgendaActive = ($currentScript === 'research_agenda.php');
$isCapabilitiesActive = ($currentScript === 'capabilities.php');
$isConfigActive = ($currentScript === 'configuration.php');
?>
<nav class="navbar navbar-expand-lg navbar-dark bg-dark sticky-top shadow-sm">
    <div class="container-fluid">
        <a class="navbar-brand d-flex align-items-center fw-bold" href="projects.php">
            <i class="bi bi-cpu text-primary me-2"></i>
            <span>Biodiversity AI Scientist</span>
        </a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#topSharedNavbar" aria-controls="topSharedNavbar" aria-expanded="false" aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
        </button>
        
        <div class="collapse navbar-collapse" id="topSharedNavbar">
            <div class="navbar-nav me-auto">
                <a class="nav-link <?= $isProjectsActive ? 'active fw-semibold' : '' ?>" href="projects.php">
                    <i class="bi bi-folder2-open me-1"></i>Projects
                </a>
                <a class="nav-link <?= $isAgendaActive ? 'active fw-semibold' : '' ?>" href="research_agenda.php<?= $projParam ?>">
                    <i class="bi bi-journal-bookmark me-1"></i>Research Agenda
                </a>
                <a class="nav-link <?= $isCapabilitiesActive ? 'active fw-semibold' : '' ?>" href="capabilities.php<?= $projParam ?>">
                    <i class="bi bi-tools me-1"></i>Capabilities &amp; Tools
                </a>
                <a class="nav-link <?= $isConfigActive ? 'active fw-semibold' : '' ?>" href="configuration.php">
                    <i class="bi bi-gear me-1"></i>Configuration
                </a>
                <a class="nav-link" href="help/index.php<?= $projParam ?>">
                    <i class="bi bi-question-circle me-1"></i>Help
                </a>
            </div>

            <?php if ($currentProjectId > 0): ?>
                <div class="d-flex align-items-center gap-2">
                    <span class="badge bg-primary-subtle text-primary border border-primary-subtle px-2 py-1">
                        <i class="bi bi-folder-check me-1"></i>Project #<?= $currentProjectId ?>
                        <?php if (!empty($project['title'])): ?>
                            &mdash; <?= htmlspecialchars(mb_strimwidth($project['title'], 0, 30, '...'), ENT_QUOTES, 'UTF-8') ?>
                        <?php endif; ?>
                    </span>
                    <?php if ($currentScript !== 'project.php'): ?>
                        <a href="project.php?project_id=<?= $currentProjectId ?>" class="btn btn-sm btn-outline-light" title="Project Overview">
                            <i class="bi bi-arrow-return-left me-1"></i>Overview
                        </a>
                    <?php endif; ?>
                </div>
            <?php endif; ?>
        </div>
    </div>
</nav>
