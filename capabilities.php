<?php

declare(strict_types=1);

require_once __DIR__ . '/includes/api.php';
require_once __DIR__ . '/includes/functions.php';

$projectId = isset($_GET['project_id']) && is_numeric($_GET['project_id']) && (int)$_GET['project_id'] > 0 
    ? (int)$_GET['project_id'] 
    : null;

$project = null;
$error = null;
$notice = null;
$selectedCategory = trim($_GET['category'] ?? '');

try {
    if ($projectId !== null) {
        $project = api_get('/projects/' . $projectId);
    }

    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        $action = trim($_POST['action'] ?? '');

        if ($action === 'create_application') {
            $name = trim($_POST['name'] ?? '');
            $displayName = trim($_POST['display_name'] ?? '');
            $category = trim($_POST['category'] ?? 'vision_ml');
            $description = trim($_POST['description'] ?? '');
            $hostEnv = trim($_POST['host_environment'] ?? 'Local Host');
            $invType = trim($_POST['invocation_type'] ?? 'cli_script');
            $interfaceUrl = trim($_POST['interface_url'] ?? '');
            $isGpu = !empty($_POST['is_gpu_required']);
            $timeout = filter_input(INPUT_POST, 'execution_timeout_seconds', FILTER_VALIDATE_INT) ?: null;

            api_post('/applications', [
                'name' => $name,
                'display_name' => $displayName,
                'category' => $category,
                'description' => $description,
                'host_environment' => $hostEnv,
                'invocation_type' => $invType,
                'interface_url' => $interfaceUrl ?: null,
                'is_gpu_required' => $isGpu,
                'execution_timeout_seconds' => $timeout,
                'is_enabled' => true,
                'capabilities' => []
            ]);

            $redir = 'capabilities.php?' . ($projectId ? 'project_id=' . $projectId . '&' : '') . 'app_created=1' . ($selectedCategory ? '&category=' . urlencode($selectedCategory) : '');
            header('Location: ' . $redir);
            exit;
        } elseif ($action === 'update_application') {
            $appId = filter_input(INPUT_POST, 'application_id', FILTER_VALIDATE_INT);
            $displayName = trim($_POST['display_name'] ?? '');
            $category = trim($_POST['category'] ?? 'vision_ml');
            $description = trim($_POST['description'] ?? '');
            $hostEnv = trim($_POST['host_environment'] ?? 'Local Host');
            $invType = trim($_POST['invocation_type'] ?? 'cli_script');
            $interfaceUrl = trim($_POST['interface_url'] ?? '');
            $isGpu = !empty($_POST['is_gpu_required']);
            $isEnabled = !empty($_POST['is_enabled']);

            if ($appId) {
                api_patch('/applications/' . $appId, [
                    'display_name' => $displayName ?: null,
                    'category' => $category ?: null,
                    'description' => $description ?: null,
                    'host_environment' => $hostEnv ?: null,
                    'invocation_type' => $invType ?: null,
                    'interface_url' => $interfaceUrl ?: null,
                    'is_gpu_required' => $isGpu,
                    'is_enabled' => $isEnabled,
                ]);

                $redir = 'capabilities.php?' . ($projectId ? 'project_id=' . $projectId . '&' : '') . 'app_updated=1' . ($selectedCategory ? '&category=' . urlencode($selectedCategory) : '');
                header('Location: ' . $redir);
                exit;
            }
        } elseif ($action === 'add_capability') {
            $appId = filter_input(INPUT_POST, 'application_id', FILTER_VALIDATE_INT);
            $capKey = trim($_POST['capability_key'] ?? '');
            $displayName = trim($_POST['display_name'] ?? '');
            $domain = trim($_POST['domain'] ?? 'biodiversity_informatics');
            $subdomain = trim($_POST['subdomain'] ?? '');
            $ebvDim = trim($_POST['ebv_dimension'] ?? '');
            $purpose = trim($_POST['scientific_purpose'] ?? '');
            $tasks = trim($_POST['scientific_tasks'] ?? '');
            $duration = trim($_POST['typical_duration'] ?? '1–5 minutes');
            $repro = trim($_POST['reproducibility_level'] ?? 'deterministic');
            $isGeneric = !empty($_POST['is_generic']);
            $modData = !empty($_POST['modifies_data']);
            $rawParams = trim($_POST['default_parameters'] ?? '{}');
            $params = json_decode($rawParams, true) ?: [];

            if ($appId) {
                api_post('/applications/' . $appId . '/capabilities', [
                    'capability_key' => $capKey,
                    'display_name' => $displayName,
                    'domain' => $domain,
                    'subdomain' => $subdomain ?: null,
                    'ebv_dimension' => $ebvDim ?: null,
                    'scientific_purpose' => $purpose,
                    'scientific_tasks' => $tasks ?: null,
                    'typical_duration' => $duration ?: null,
                    'reproducibility_level' => $repro,
                    'is_generic' => $isGeneric,
                    'modifies_data' => $modData,
                    'creates_result' => true,
                    'creates_artifact' => true,
                    'creates_dataset_version' => false,
                    'default_parameters' => $params,
                    'is_enabled' => true
                ]);

                $redir = 'capabilities.php?' . ($projectId ? 'project_id=' . $projectId . '&' : '') . 'cap_created=1' . ($selectedCategory ? '&category=' . urlencode($selectedCategory) : '');
                header('Location: ' . $redir);
                exit;
            }
        } elseif ($action === 'update_capability') {
            $capId = filter_input(INPUT_POST, 'capability_id', FILTER_VALIDATE_INT);
            $displayName = trim($_POST['display_name'] ?? '');
            $domain = trim($_POST['domain'] ?? 'biodiversity_informatics');
            $subdomain = trim($_POST['subdomain'] ?? '');
            $ebvDim = trim($_POST['ebv_dimension'] ?? '');
            $purpose = trim($_POST['scientific_purpose'] ?? '');
            $tasks = trim($_POST['scientific_tasks'] ?? '');
            $duration = trim($_POST['typical_duration'] ?? '1–5 minutes');
            $repro = trim($_POST['reproducibility_level'] ?? 'deterministic');
            $capScope = trim($_POST['capability_scope'] ?? '');
            $isGeneric = !empty($_POST['is_generic']);
            $isEnabled = !empty($_POST['is_enabled']);
            $availability = trim($_POST['availability'] ?? 'installed');
            $knowledgeStatus = trim($_POST['knowledge_status'] ?? 'known');

            if ($capId) {
                api_patch('/capabilities/' . $capId, [
                    'display_name' => $displayName ?: null,
                    'domain' => $domain ?: null,
                    'subdomain' => $subdomain ?: null,
                    'ebv_dimension' => $ebvDim ?: null,
                    'scientific_purpose' => $purpose ?: null,
                    'scientific_tasks' => $tasks ?: null,
                    'typical_duration' => $duration ?: null,
                    'reproducibility_level' => $repro ?: null,
                    'capability_scope' => $capScope ?: 'none',
                    'is_generic' => $isGeneric,
                    'is_enabled' => $isEnabled,
                    'availability' => $availability ?: null,
                    'knowledge_status' => $knowledgeStatus ?: null,
                ]);

                $redir = 'capabilities.php?' . ($projectId ? 'project_id=' . $projectId . '&' : '') . 'cap_updated=1' . ($selectedCategory ? '&category=' . urlencode($selectedCategory) : '');
                header('Location: ' . $redir);
                exit;
            }
        } elseif ($action === 'add_implementation') {
            $capId = filter_input(INPUT_POST, 'capability_id', FILTER_VALIDATE_INT);
            $implKey = trim($_POST['implementation_key'] ?? '');
            $displayName = trim($_POST['display_name'] ?? '');
            $provider = trim($_POST['provider'] ?? 'core_engine');
            $adapterModule = trim($_POST['adapter_module'] ?? '');
            $backendEnv = trim($_POST['backend_environment'] ?? 'local_host');
            $runtimeVersion = trim($_POST['runtime_version'] ?? '1.0.0');
            $scope = trim($_POST['implementation_scope'] ?? 'generic_core');
            $availability = trim($_POST['availability'] ?? 'installed');
            $valStatus = trim($_POST['validation_status'] ?? 'known');
            $isDefault = !empty($_POST['is_default']);

            if ($capId && $implKey) {
                api_post('/capabilities/' . $capId . '/implementations', [
                    'implementation_key' => $implKey,
                    'display_name' => $displayName ?: $implKey,
                    'provider' => $provider,
                    'adapter_module' => $adapterModule ?: null,
                    'backend_environment' => $backendEnv,
                    'runtime_version' => $runtimeVersion ?: null,
                    'implementation_scope' => $scope,
                    'availability' => $availability,
                    'validation_status' => $valStatus,
                    'is_default' => $isDefault,
                ]);

                $redir = 'capabilities.php?' . ($projectId ? 'project_id=' . $projectId . '&' : '') . 'impl_created=1' . ($selectedCategory ? '&category=' . urlencode($selectedCategory) : '');
                header('Location: ' . $redir);
                exit;
            }
        } elseif ($action === 'update_implementation') {
            $implId = filter_input(INPUT_POST, 'implementation_id', FILTER_VALIDATE_INT);
            $displayName = trim($_POST['display_name'] ?? '');
            $provider = trim($_POST['provider'] ?? 'core_engine');
            $adapterModule = trim($_POST['adapter_module'] ?? '');
            $backendEnv = trim($_POST['backend_environment'] ?? 'local_host');
            $runtimeVersion = trim($_POST['runtime_version'] ?? '1.0.0');
            $scope = trim($_POST['implementation_scope'] ?? 'generic_core');
            $availability = trim($_POST['availability'] ?? 'installed');
            $valStatus = trim($_POST['validation_status'] ?? 'known');
            $isDefault = !empty($_POST['is_default']);

            if ($implId) {
                api_patch('/implementations/' . $implId, [
                    'display_name' => $displayName ?: null,
                    'provider' => $provider ?: null,
                    'adapter_module' => $adapterModule ?: null,
                    'backend_environment' => $backendEnv ?: null,
                    'runtime_version' => $runtimeVersion ?: null,
                    'implementation_scope' => $scope ?: null,
                    'availability' => $availability ?: null,
                    'validation_status' => $valStatus ?: null,
                    'is_default' => $isDefault,
                ]);

                $redir = 'capabilities.php?' . ($projectId ? 'project_id=' . $projectId . '&' : '') . 'impl_updated=1' . ($selectedCategory ? '&category=' . urlencode($selectedCategory) : '');
                header('Location: ' . $redir);
                exit;
            }
        } elseif ($action === 'seed_taxonomy') {
            api_post('/capabilities/seed-taxonomy', []);
            $redir = 'capabilities.php?' . ($projectId ? 'project_id=' . $projectId . '&' : '') . 'seeded=1';
            header('Location: ' . $redir);
            exit;
        } elseif ($action === 'resolve_gap') {
            $gapId = filter_input(INPUT_POST, 'gap_id', FILTER_VALIDATE_INT);
            $status = trim($_POST['status'] ?? 'resolved');
            $notes = trim($_POST['resolution_notes'] ?? '');
            if ($gapId) {
                api_patch('/capability-gaps/' . $gapId, [
                    'status' => $status,
                    'resolution_notes' => $notes ?: null,
                ]);
                $redir = 'capabilities.php?' . ($projectId ? 'project_id=' . $projectId . '&' : '') . 'gap_updated=1&category=gaps';
                header('Location: ' . $redir);
                exit;
            }
        }
    }

    if (isset($_GET['app_created'])) {
        $notice = 'New Scientific Application registered in the software inventory!';
    } elseif (isset($_GET['app_updated'])) {
        $notice = 'Scientific Application settings updated successfully!';
    } elseif (isset($_GET['cap_created'])) {
        $notice = 'New Scientific Capability successfully added to application!';
    } elseif (isset($_GET['cap_updated'])) {
        $notice = 'Scientific Capability metadata and properties updated!';
    } elseif (isset($_GET['impl_created'])) {
        $notice = 'New Implementation Adapter bound to capability successfully!';
    } elseif (isset($_GET['impl_updated'])) {
        $notice = 'Implementation Adapter properties and availability updated!';
    } elseif (isset($_GET['seeded'])) {
        $notice = 'Canonical 14-Domain Biodiversity Taxonomy & Implementations synchronized successfully!';
    } elseif (isset($_GET['gap_updated'])) {
        $notice = 'Capability Gap status and resolution notes updated!';
    }

    $selectedScope = trim($_GET['scope'] ?? '');
    $selectedDomain = trim($_GET['domain'] ?? '');

    $appEndpoint = '/applications' . ($selectedCategory && $selectedCategory !== 'gaps' ? '?category=' . urlencode($selectedCategory) : '');
    $applications = api_get($appEndpoint);
    
    $capEndpoint = '/capabilities' . ($selectedScope ? '?scope=' . urlencode($selectedScope) : '');
    $allCapabilities = api_get($capEndpoint);
    $domains = api_get('/capabilities/domains') ?: [];
    $semanticTypes = api_get('/capabilities/semantic-types') ?: [];
    $coverageMatrix = api_get('/capabilities/coverage-matrix') ?: null;
    
    $capabilityGaps = $projectId ? api_get('/projects/' . $projectId . '/capability-gaps') : [];
    if (!is_array($capabilityGaps)) $capabilityGaps = [];

} catch (Throwable $e) {
    $error = $e->getMessage();
    $applications = [];
    $allCapabilities = [];
    $domains = [];
    $semanticTypes = [];
    $coverageMatrix = null;
    $capabilityGaps = [];
}

$activePage = 'capabilities';
$pageQuery = $projectId ? '?project_id=' . $projectId : '';

?>
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Scientific Software Inventory &amp; Capabilities - Biodiversity AI Scientist</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="css/app.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
</head>
<body class="bg-light">

<?php require_once __DIR__ . '/includes/navbar.php'; ?>


<div class="container-fluid">
    <?php if ($project !== null): ?>
        <div class="row border-bottom bg-white">
            <div class="col-12 px-4 py-3">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <div class="text-muted small mb-1">Research Project #<?= (int)$project['id'] ?></div>
                        <h1 class="h4 mb-0"><?= h($project['title']) ?></h1>
                    </div>
                    <div>
                        <a href="project.php?project_id=<?= $projectId ?>" class="btn btn-sm btn-outline-secondary">
                            Project overview
                        </a>
                    </div>
                </div>
            </div>
        </div>
    <?php endif; ?>

    <div class="row">
        <?php if ($projectId !== null): ?>
            <?php require __DIR__ . '/includes/menu.php'; ?>
            <main class="col-md-9 col-lg-10 p-4">
        <?php else: ?>
            <main class="col-12 p-4 max-w-7xl mx-auto" style="max-width: 1300px;">
        <?php endif; ?>

            <div class="d-flex justify-content-between align-items-start mb-4 flex-wrap gap-2">
                <div>
                    <div class="d-flex align-items-center gap-2 mb-1">
                        <span class="badge bg-primary text-uppercase tracking-wide">Platform Toolbox</span>
                        <h2 class="h3 mb-0 fw-bold">Scientific Software Ecosystem &amp; Capability Registry</h2>
                    </div>
                    <p class="text-muted mb-0">
                        Global repository of available scientific software, GPU pipelines, CLI tools, external biological APIs, and statistical methods shared across all projects.
                    </p>
                </div>
                <div class="d-flex align-items-center gap-2 flex-wrap">
                    <span class="badge bg-light text-dark border fs-6">
                        <?= count($applications) ?> Application<?= count($applications) === 1 ? '' : 's' ?> / <?= count($allCapabilities) ?> Capabilities
                    </span>
                    <form method="post" action="capabilities.php<?= $pageQuery ?>" class="d-inline" onsubmit="return confirm('Synchronize canonical 14-domain biodiversity taxonomy & implementations?');">
                        <input type="hidden" name="action" value="seed_taxonomy">
                        <button type="submit" class="btn btn-outline-secondary btn-sm fw-semibold shadow-sm">
                            <i class="bi bi-arrow-repeat me-1"></i> Sync / Re-seed Registry
                        </button>
                    </form>
                    <button type="button" class="btn btn-primary btn-sm fw-semibold shadow-sm" data-bs-toggle="modal" data-bs-target="#registerAppModal">
                        + Register Application / Tool
                    </button>
                </div>
            </div>

            <!-- Explanatory Banner -->
            <div class="alert alert-info shadow-sm mb-4">
                <strong>🏛️ Grounded Software Inventory (Shared Across All Projects):</strong>
                This inventory catalogs the real scientific software environment (local/remote GPU nodes, domain web pipelines, external taxonomic APIs, and statistical suites). 
                Any project can pre-specify <strong>Experiments</strong> and execute <strong>Experiment Runs</strong> against these registered capabilities.
            </div>

            <?php if ($notice !== null): ?>
                <div class="alert alert-success alert-dismissible fade show mb-4" role="alert">
                    <?= h($notice) ?>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            <?php endif; ?>

            <?php if ($error !== null): ?>
                <div class="alert alert-danger alert-dismissible fade show mb-4" role="alert">
                    <strong>Error:</strong> <?= h($error) ?>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            <?php endif; ?>

            <!-- Scope Filter Buttons (4-Tier Scope Tagging) -->
            <div class="card shadow-sm border-0 mb-4 bg-white">
                <div class="card-body p-3">
                    <div class="d-flex flex-wrap justify-content-between align-items-center gap-2">
                        <div class="d-flex flex-wrap align-items-center gap-2">
                            <span class="fw-bold text-dark small me-1"><i class="bi bi-funnel-fill text-primary me-1"></i>Scope Filter:</span>
                            <a href="capabilities.php<?= $projectId ? '?project_id=' . $projectId : '' ?>" class="btn btn-sm <?= empty($selectedScope) ? 'btn-dark' : 'btn-outline-secondary' ?>">
                                All Scopes
                            </a>
                            <a href="capabilities.php?<?= $projectId ? 'project_id=' . $projectId . '&' : '' ?>scope=generic_core" class="btn btn-sm <?= $selectedScope === 'generic_core' ? 'btn-primary' : 'btn-outline-primary' ?>">
                                🌐 Generic Core
                            </a>
                            <a href="capabilities.php?<?= $projectId ? 'project_id=' . $projectId . '&' : '' ?>scope=identifyshell_specific" class="btn btn-sm <?= $selectedScope === 'identifyshell_specific' ? 'btn-success' : 'btn-outline-success' ?>">
                                🐚 IdentifyShell Specific
                            </a>
                            <a href="capabilities.php?<?= $projectId ? 'project_id=' . $projectId . '&' : '' ?>scope=official_extension" class="btn btn-sm <?= $selectedScope === 'official_extension' ? 'btn-info text-white' : 'btn-outline-info text-dark' ?>">
                                🧩 Official Extensions
                            </a>
                            <a href="capabilities.php?<?= $projectId ? 'project_id=' . $projectId . '&' : '' ?>scope=external_tool" class="btn btn-sm <?= $selectedScope === 'external_tool' ? 'btn-warning text-dark' : 'btn-outline-warning text-dark' ?>">
                                ⚙️ External Tools
                            </a>
                        </div>
                        <?php if (!empty($domains)): ?>
                            <span class="badge bg-light text-dark border small">
                                📚 14 Biodiversity Domains Active
                            </span>
                        <?php endif; ?>
                    </div>
                </div>
            </div>

            <!-- Category Filter Tabs -->
            <div class="mb-4">
                <ul class="nav nav-pills">
                    <li class="nav-item">
                        <a class="nav-link <?= empty($selectedCategory) ? 'active' : '' ?>" href="capabilities.php<?= $projectId ? '?project_id=' . $projectId : '' ?><?= $selectedScope ? '&scope=' . urlencode($selectedScope) : '' ?>">
                            All Applications (<?= count($applications) ?>)
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link <?= $selectedCategory === 'coverage' ? 'active' : '' ?>" href="capabilities.php?<?= $projectId ? 'project_id=' . $projectId . '&' : '' ?>category=coverage">
                            📊 Coverage Matrix (14 Domains)
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link <?= $selectedCategory === 'identifyshell_specific' ? 'active' : '' ?>" href="capabilities.php?<?= $projectId ? 'project_id=' . $projectId . '&' : '' ?>category=identifyshell_specific<?= $selectedScope ? '&scope=' . urlencode($selectedScope) : '' ?>">
                            🐚 IdentifyShell Specific
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link <?= $selectedCategory === 'vision_ml' ? 'active' : '' ?>" href="capabilities.php?<?= $projectId ? 'project_id=' . $projectId . '&' : '' ?>category=vision_ml<?= $selectedScope ? '&scope=' . urlencode($selectedScope) : '' ?>">
                            🖼️ Vision &amp; Deep Learning
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link <?= $selectedCategory === 'taxonomy' ? 'active' : '' ?>" href="capabilities.php?<?= $projectId ? 'project_id=' . $projectId . '&' : '' ?>category=taxonomy<?= $selectedScope ? '&scope=' . urlencode($selectedScope) : '' ?>">
                            🏷️ Taxonomy &amp; Nomenclature
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link <?= $selectedCategory === 'statistics' ? 'active' : '' ?>" href="capabilities.php?<?= $projectId ? 'project_id=' . $projectId . '&' : '' ?>category=statistics<?= $selectedScope ? '&scope=' . urlencode($selectedScope) : '' ?>">
                            📊 Morphometrics &amp; Statistics
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link <?= $selectedCategory === 'dataset' ? 'active' : '' ?>" href="capabilities.php?<?= $projectId ? 'project_id=' . $projectId . '&' : '' ?>category=dataset<?= $selectedScope ? '&scope=' . urlencode($selectedScope) : '' ?>">
                            📦 Dataset Governance
                        </a>
                    </li>
                    <?php if ($projectId !== null): ?>
                        <li class="nav-item">
                            <a class="nav-link <?= $selectedCategory === 'gaps' ? 'active text-white bg-danger' : 'text-danger' ?>" href="capabilities.php?project_id=<?= $projectId ?>&category=gaps">
                                ⚠️ Capability Gaps (<?= count($capabilityGaps) ?>)
                            </a>
                        </li>
                    <?php endif; ?>
                </ul>
            </div>

            <!-- Biodiversity Coverage Matrix View -->
            <?php if ($selectedCategory === 'coverage'): ?>
                <div class="card shadow-sm border-0 mb-4 bg-white">
                    <div class="card-header bg-white py-3 d-flex justify-content-between align-items-center">
                        <h5 class="fw-bold mb-0 text-dark"><i class="bi bi-grid-3x3-gap-fill text-success me-2"></i>Biodiversity Capability Coverage Matrix</h5>
                        <?php if ($coverageMatrix): ?>
                            <div class="d-flex gap-2 small">
                                <span class="badge bg-primary"><?= (int)$coverageMatrix['total_known_specs'] ?> Known Methods</span>
                                <span class="badge bg-success"><?= (int)$coverageMatrix['total_installed'] ?> Installed</span>
                                <span class="badge bg-secondary"><?= (int)$coverageMatrix['total_gaps'] ?> Open Gaps</span>
                            </div>
                        <?php endif; ?>
                    </div>
                    <div class="card-body p-0">
                        <div class="table-responsive">
                            <table class="table table-bordered table-striped table-sm align-middle small mb-0">
                                <thead class="table-light text-center">
                                    <tr>
                                        <th class="text-start">Biodiversity Domain</th>
                                        <th>EBV Alignment</th>
                                        <th>Known Specs</th>
                                        <th>Installed (Local)</th>
                                        <th>Validated</th>
                                        <th>Extensions</th>
                                        <th>External Tools</th>
                                        <th>Gaps</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <?php if ($coverageMatrix && !empty($coverageMatrix['domains'])): ?>
                                        <?php 
                                        $totKnown = 0; $totInst = 0; $totVal = 0; $totExt = 0; $totExtern = 0; $totGaps = 0;
                                        foreach ($coverageMatrix['domains'] as $dom): 
                                            $totKnown += (int)$dom['known_specs_count'];
                                            $totInst += (int)$dom['installed_count'];
                                            $totVal += (int)$dom['validated_count'];
                                            $totExt += (int)$dom['extension_count'];
                                            $totExtern += (int)$dom['external_count'];
                                            $totGaps += (int)$dom['gap_count'];
                                        ?>
                                            <tr>
                                                <td class="fw-bold"><?= h($dom['display_name']) ?></td>
                                                <td class="text-center"><span class="badge bg-light text-dark border"><?= h($dom['ebv_dimension'] ?? 'Cross-cutting') ?></span></td>
                                                <td class="text-center fw-bold"><?= (int)$dom['known_specs_count'] ?></td>
                                                <td class="text-center"><span class="badge bg-success"><?= (int)$dom['installed_count'] ?></span></td>
                                                <td class="text-center"><span class="badge bg-info text-dark"><?= (int)$dom['validated_count'] ?></span></td>
                                                <td class="text-center"><span class="badge text-white" style="background-color:#6f42c1;"><?= (int)$dom['extension_count'] ?></span></td>
                                                <td class="text-center"><span class="badge bg-warning text-dark"><?= (int)$dom['external_count'] ?></span></td>
                                                <td class="text-center"><span class="badge bg-secondary"><?= (int)$dom['gap_count'] ?></span></td>
                                            </tr>
                                        <?php endforeach; ?>
                                    <?php endif; ?>
                                </tbody>
                                <tfoot class="table-secondary fw-bold text-center">
                                    <tr>
                                        <td class="text-start">Total (14 Domains Reconciled)</td>
                                        <td>100% Core EBVs</td>
                                        <td><?= $totKnown ?></td>
                                        <td><span class="badge bg-success"><?= $totInst ?></span></td>
                                        <td><span class="badge bg-info text-dark"><?= $totVal ?></span></td>
                                        <td><span class="badge text-white" style="background-color:#6f42c1;"><?= $totExt ?></span></td>
                                        <td><span class="badge bg-warning text-dark"><?= $totExtern ?></span></td>
                                        <td><span class="badge bg-secondary"><?= $totGaps ?></span></td>
                                    </tr>
                                </tfoot>
                            </table>
                        </div>
                    </div>
                </div>
            <?php endif; ?>

            <!-- Capability Gaps View -->
            <?php if ($selectedCategory === 'gaps'): ?>
                <?php if (empty($capabilityGaps)): ?>
                    <div class="card shadow-sm text-center py-5">
                        <div class="card-body">
                            <i class="bi bi-check-circle text-success fs-1 mb-2"></i>
                            <h3 class="h5">No Capability Gaps Identified</h3>
                            <p class="text-muted mb-0">All investigation steps have registered software capabilities or no gaps have been flagged.</p>
                        </div>
                    </div>
                <?php else: ?>
                    <div class="d-flex flex-column gap-3 mb-5">
                        <?php foreach ($capabilityGaps as $gap): ?>
                            <div class="card shadow-sm border <?= $gap['status'] === 'unresolved' ? 'border-danger-subtle' : 'border-success-subtle' ?>">
                                <div class="card-header bg-white d-flex justify-content-between align-items-center">
                                    <div>
                                        <span class="badge bg-dark me-2">Gap #<?= $gap['id'] ?></span>
                                        <span class="badge <?= $gap['status'] === 'unresolved' ? 'bg-danger' : 'bg-success' ?> text-uppercase">
                                            <?= htmlspecialchars($gap['status'], ENT_QUOTES, 'UTF-8') ?>
                                        </span>
                                    </div>
                                    <span class="text-muted small">
                                        Identified: <?= htmlspecialchars($gap['identified_at'] ?? '', ENT_QUOTES, 'UTF-8') ?>
                                    </span>
                                </div>
                                <div class="card-body">
                                    <h5 class="fw-bold text-danger mb-2">
                                        <i class="bi bi-exclamation-triangle-fill me-1"></i>Scientific Requirement:
                                    </h5>
                                    <p class="mb-3 text-dark"><?= htmlspecialchars($gap['scientific_requirement'], ENT_QUOTES, 'UTF-8') ?></p>

                                    <?php if (!empty($gap['resolution_notes'])): ?>
                                        <div class="p-2 bg-light rounded border mb-3 small">
                                            <strong>Resolution Notes:</strong> <?= htmlspecialchars($gap['resolution_notes'], ENT_QUOTES, 'UTF-8') ?>
                                        </div>
                                    <?php endif; ?>

                                    <form method="post" action="capabilities.php<?= $pageQuery ?>" class="row g-2 align-items-center">
                                        <input type="hidden" name="action" value="resolve_gap">
                                        <input type="hidden" name="gap_id" value="<?= (int)$gap['id'] ?>">
                                        <div class="col-auto">
                                            <select name="status" class="form-select form-select-sm">
                                                <option value="resolved" <?= $gap['status'] === 'resolved' ? 'selected' : '' ?>>Mark Resolved</option>
                                                <option value="in_progress" <?= $gap['status'] === 'in_progress' ? 'selected' : '' ?>>In Progress</option>
                                                <option value="waived" <?= $gap['status'] === 'waived' ? 'selected' : '' ?>>Waive / Skip</option>
                                            </select>
                                        </div>
                                        <div class="col">
                                            <input type="text" name="resolution_notes" class="form-control form-control-sm" placeholder="Add resolution note (e.g. registered new adapter)" value="<?= htmlspecialchars($gap['resolution_notes'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
                                        </div>
                                        <div class="col-auto">
                                            <button type="submit" class="btn btn-sm btn-primary">Update Gap</button>
                                        </div>
                                    </form>
                                </div>
                            </div>
                        <?php endforeach; ?>
                    </div>
                <?php endif; ?>
            <?php endif; ?>

            <!-- Application Cards List -->
            <?php if (empty($applications)): ?>
                <div class="card shadow-sm text-center py-5">
                    <div class="card-body">
                        <h3 class="h5">No applications found</h3>
                        <p class="text-muted mb-0">No tools match the selected category filter.</p>
                    </div>
                </div>
            <?php else: ?>
                <div class="d-flex flex-column gap-4">
                    <?php foreach ($applications as $app): ?>
                        <div class="card shadow-sm border-0 border-top border-4 border-primary">
                            <div class="card-header bg-white py-3 d-flex justify-content-between align-items-center flex-wrap gap-2">
                                <div>
                                    <div class="d-flex align-items-center gap-2">
                                        <h3 class="h5 mb-0 fw-bold text-dark">
                                            <?= h($app['display_name']) ?>
                                        </h3>
                                        <code class="text-muted small">[<?= h($app['name']) ?>]</code>
                                        <?php if ($app['category'] === 'identifyshell_specific'): ?>
                                            <span class="badge bg-success">🐚 IdentifyShell Specific</span>
                                        <?php else: ?>
                                            <span class="badge bg-secondary"><?= h(ucwords(str_replace('_', ' ', $app['category']))) ?></span>
                                        <?php endif; ?>
                                    </div>
                                    <div class="text-muted small mt-1">
                                        📍 <strong>Host:</strong> <?= h($app['host_environment']) ?>
                                    </div>
                                </div>
                                <div class="d-flex align-items-center gap-2 flex-wrap">
                                    <span class="badge <?= $app['is_gpu_required'] ? 'bg-danger' : 'bg-secondary' ?>">
                                        <?= $app['is_gpu_required'] ? '⚡ GPU Required (CUDA)' : '💻 CPU Only' ?>
                                    </span>
                                    <span class="badge bg-light text-dark border">
                                        🎮 <?= h(ucwords(str_replace('_', ' ', $app['invocation_type']))) ?>
                                    </span>
                                    <?php if (!empty($app['interface_url'])): ?>
                                        <a href="<?= h($app['interface_url']) ?>" target="_blank" class="btn btn-sm btn-outline-primary fw-semibold">
                                            Open External App ↗
                                        </a>
                                    <?php endif; ?>
                                    <button type="button" class="btn btn-sm btn-outline-secondary" data-bs-toggle="modal" data-bs-target="#editAppModal<?= (int)$app['id'] ?>">
                                        <i class="bi bi-pencil me-1"></i> Edit App
                                    </button>
                                    <button type="button" class="btn btn-sm btn-primary" data-bs-toggle="modal" data-bs-target="#addCapModal<?= (int)$app['id'] ?>">
                                        + Add Capability
                                    </button>
                                </div>
                            </div>
                            <div class="card-body">
                                <p class="text-secondary small mb-3">
                                    <?= nl2br(h($app['description'])) ?>
                                </p>

                                <h4 class="h6 fw-bold text-uppercase text-muted small border-bottom pb-2 mb-3">
                                    Exposed Scientific Capabilities (<?= count($app['capabilities']) ?>)
                                </h4>

                                <?php if (empty($app['capabilities'])): ?>
                                    <div class="text-muted small fst-italic">No capabilities registered under this application yet.</div>
                                <?php else: ?>
                                    <div class="row g-3">
                                        <?php foreach ($app['capabilities'] as $cap): ?>
                                            <?php
                                             $scope = $cap['capability_scope'] ?? '';
                                             $domainName = !empty($cap['domain']) ? ucwords(str_replace('_', ' ', $cap['domain'])) : 'Informatics';
                                             $impls = $cap['implementations'] ?? [];
                                            ?>
                                            <div class="col-lg-6">
                                                <div class="card h-100 bg-light border">
                                                    <div class="card-body p-3 d-flex flex-column justify-content-between">
                                                        <div>
                                                            <div class="d-flex justify-content-between align-items-start gap-2 mb-2">
                                                                <div>
                                                                    <div class="fw-bold text-primary">
                                                                        <?= h($cap['display_name']) ?>
                                                                    </div>
                                                                    <code class="small text-muted"><?= h($cap['capability_key']) ?></code>
                                                                </div>
                                                                <div class="d-flex flex-column align-items-end gap-1">
                                                                    <?php if ($scope === 'generic_core'): ?>
                                                                        <span class="badge bg-primary">🌐 Generic Core</span>
                                                                    <?php elseif ($scope === 'identifyshell_specific'): ?>
                                                                        <span class="badge bg-success">🐚 IdentifyShell Specific</span>
                                                                    <?php elseif ($scope === 'official_extension'): ?>
                                                                        <span class="badge text-white" style="background-color:#6f42c1;">🧩 Extension</span>
                                                                    <?php elseif ($scope === 'external_tool'): ?>
                                                                        <span class="badge bg-warning text-dark">⚙️ External Tool</span>
                                                                    <?php endif; ?>
                                                                    <span class="badge bg-secondary bg-opacity-10 text-secondary border small">
                                                                        <?= h($domainName) ?>
                                                                    </span>
                                                                </div>
                                                            </div>
                                                            <p class="small text-secondary mb-2">
                                                                <?= h($cap['scientific_purpose']) ?>
                                                            </p>

                                                            <!-- Attached Implementations (Two-Tier Model) -->
                                                            <div class="mb-2 p-2 bg-white rounded border">
                                                                <div class="d-flex justify-content-between align-items-center mb-1">
                                                                    <span class="small fw-bold text-dark">
                                                                        <i class="bi bi-cpu text-primary me-1"></i>Bound Adapters (<?= count($impls) ?>):
                                                                    </span>
                                                                    <button type="button" class="btn btn-sm btn-link p-0 text-decoration-none small" data-bs-toggle="modal" data-bs-target="#addImplModal<?= (int)$cap['id'] ?>">
                                                                        + Bind Adapter
                                                                    </button>
                                                                </div>
                                                                <?php if (empty($impls)): ?>
                                                                    <div class="text-muted small fst-italic">No physical implementations bound.</div>
                                                                <?php else: ?>
                                                                    <div class="d-flex flex-column gap-1">
                                                                        <?php foreach ($impls as $im): ?>
                                                                            <div class="d-flex justify-content-between align-items-center small font-monospace bg-light p-1 rounded">
                                                                                <span><code><?= h($im['implementation_key']) ?></code> <span class="text-muted">(<?= h($im['implementation_scope'] ?? 'core') ?>)</span></span>
                                                                                <div class="d-flex align-items-center gap-1">
                                                                                    <span class="badge <?= $im['availability'] === 'installed' ? 'bg-success' : 'bg-secondary' ?>">
                                                                                        <?= h($im['availability']) ?>
                                                                                    </span>
                                                                                    <button type="button" class="btn btn-sm btn-link text-muted p-0" data-bs-toggle="modal" data-bs-target="#editImplModal<?= (int)$im['id'] ?>" title="Edit Implementation">
                                                                                        <i class="bi bi-pencil-square"></i>
                                                                                    </button>
                                                                                </div>
                                                                            </div>
                                                                        <?php endforeach; ?>
                                                                    </div>
                                                                <?php endif; ?>
                                                            </div>

                                                            <?php if (!empty($cap['expected_evidence_types'])): ?>
                                                                <div class="small text-muted mb-2">
                                                                    <strong>Evidence Types:</strong> 
                                                                    <?php foreach ($cap['expected_evidence_types'] as $ev): ?>
                                                                        <span class="badge bg-light text-dark border font-monospace small"><?= h($ev) ?></span>
                                                                    <?php endforeach; ?>
                                                                </div>
                                                            <?php endif; ?>
                                                        </div>

                                                        <div class="border-top pt-2 mt-2 d-flex justify-content-between align-items-center flex-wrap gap-2">
                                                            <div class="small text-muted">
                                                                ⏱️ <?= h($cap['typical_duration'] ?? '1–5 mins') ?> · 
                                                                <?= $cap['modifies_data'] ? '⚠️ Mutates Data' : '🛡️ Read-Only' ?>
                                                            </div>
                                                            <div class="d-flex gap-2">
                                                                <button type="button" class="btn btn-sm btn-outline-secondary" data-bs-toggle="modal" data-bs-target="#editCapModal<?= (int)$cap['id'] ?>">
                                                                    <i class="bi bi-pencil me-1"></i> Edit
                                                                </button>
                                                                <button type="button" class="btn btn-sm btn-link text-decoration-none p-0" data-bs-toggle="modal" data-bs-target="#specModal<?= (int)$cap['id'] ?>">
                                                                    Contract 🔍
                                                                </button>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>

                                            <!-- Schema Spec Modal -->
                                            <div class="modal fade" id="specModal<?= (int)$cap['id'] ?>" tabindex="-1">
                                                <div class="modal-dialog modal-lg">
                                                    <div class="modal-content">
                                                        <div class="modal-header">
                                                            <h5 class="modal-title">Capability Contract: <?= h($cap['display_name']) ?></h5>
                                                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                                        </div>
                                                        <div class="modal-body">
                                                            <div class="mb-3">
                                                                <label class="fw-bold small text-uppercase text-muted">Default Runtime Parameters (JSON)</label>
                                                                <pre class="bg-dark text-light p-3 rounded font-monospace small"><code><?= h(json_encode($cap['default_parameters'] ?? new stdClass(), JSON_PRETTY_PRINT)) ?></code></pre>
                                                            </div>
                                                            <div class="mb-3">
                                                                <label class="fw-bold small text-uppercase text-muted">Input Schema</label>
                                                                <pre class="bg-light text-dark p-3 rounded font-monospace small border"><code><?= h(json_encode($cap['input_schema'] ?? new stdClass(), JSON_PRETTY_PRINT)) ?></code></pre>
                                                            </div>
                                                            <div>
                                                                <label class="fw-bold small text-uppercase text-muted">Expected Output Schema</label>
                                                                <pre class="bg-light text-dark p-3 rounded font-monospace small border"><code><?= h(json_encode($cap['output_schema'] ?? new stdClass(), JSON_PRETTY_PRINT)) ?></code></pre>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>

                                            <!-- Edit Capability Modal -->
                                            <div class="modal fade" id="editCapModal<?= (int)$cap['id'] ?>" tabindex="-1">
                                                <div class="modal-dialog modal-lg">
                                                    <div class="modal-content">
                                                        <form method="post" action="capabilities.php<?= $pageQuery ?>">
                                                            <input type="hidden" name="action" value="update_capability">
                                                            <input type="hidden" name="capability_id" value="<?= (int)$cap['id'] ?>">
                                                            <div class="modal-header">
                                                                <h5 class="modal-title">Edit Capability: <?= h($cap['display_name']) ?></h5>
                                                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                                            </div>
                                                            <div class="modal-body">
                                                                <div class="row g-3">
                                                                    <div class="col-md-6">
                                                                        <label class="form-label fw-semibold">Display Name</label>
                                                                        <input type="text" name="display_name" class="form-control" value="<?= h($cap['display_name']) ?>" required>
                                                                    </div>
                                                                    <div class="col-md-6">
                                                                        <label class="form-label fw-semibold">Standardized Biodiversity Domain</label>
                                                                        <select name="domain" class="form-select">
                                                                            <?php foreach ($domains as $d): ?>
                                                                                <option value="<?= h($d['domain']) ?>" <?= ($cap['domain'] ?? '') === $d['domain'] ? 'selected' : '' ?>>
                                                                                    <?= h($d['display_name']) ?>
                                                                                </option>
                                                                            <?php endforeach; ?>
                                                                        </select>
                                                                    </div>
                                                                    <div class="col-12">
                                                                        <label class="form-label fw-semibold">Scientific Purpose</label>
                                                                        <textarea name="scientific_purpose" class="form-control" rows="2" required><?= h($cap['scientific_purpose']) ?></textarea>
                                                                    </div>
                                                                    <div class="col-md-6">
                                                                        <label class="form-label fw-semibold">Scientific Tasks</label>
                                                                        <input type="text" name="scientific_tasks" class="form-control" value="<?= h($cap['scientific_tasks'] ?? '') ?>">
                                                                    </div>
                                                                    <div class="col-md-3">
                                                                        <label class="form-label fw-semibold">Typical Duration</label>
                                                                        <input type="text" name="typical_duration" class="form-control" value="<?= h($cap['typical_duration'] ?? '1–5 mins') ?>">
                                                                    </div>
                                                                    <div class="col-md-3">
                                                                        <label class="form-label fw-semibold">Availability</label>
                                                                        <select name="availability" class="form-select">
                                                                            <option value="installed" <?= ($cap['availability'] ?? '') === 'installed' ? 'selected' : '' ?>>installed</option>
                                                                            <option value="not_installed" <?= ($cap['availability'] ?? '') === 'not_installed' ? 'selected' : '' ?>>not_installed</option>
                                                                            <option value="external" <?= ($cap['availability'] ?? '') === 'external' ? 'selected' : '' ?>>external</option>
                                                                        </select>
                                                                    </div>
                                                                    <div class="col-md-4">
                                                                        <label class="form-label fw-semibold">Knowledge Status</label>
                                                                        <select name="knowledge_status" class="form-select">
                                                                            <option value="known" <?= ($cap['knowledge_status'] ?? '') === 'known' ? 'selected' : '' ?>>known</option>
                                                                            <option value="implemented" <?= ($cap['knowledge_status'] ?? '') === 'implemented' ? 'selected' : '' ?>>implemented</option>
                                                                            <option value="validated" <?= ($cap['knowledge_status'] ?? '') === 'validated' ? 'selected' : '' ?>>validated</option>
                                                                        </select>
                                                                    </div>
                                                                    <div class="col-md-6">
                                                                        <label class="form-label fw-semibold">Capability Scope Badge</label>
                                                                        <select name="capability_scope" class="form-select">
                                                                            <option value="none" <?= empty($cap['capability_scope']) || $cap['capability_scope'] === 'none' ? 'selected' : '' ?>>None (Hide badge / governed by adapters)</option>
                                                                            <option value="generic_core" <?= ($cap['capability_scope'] ?? '') === 'generic_core' ? 'selected' : '' ?>>Generic Core (🌐)</option>
                                                                            <option value="official_extension" <?= ($cap['capability_scope'] ?? '') === 'official_extension' ? 'selected' : '' ?>>Official Extension (🧩)</option>
                                                                            <option value="external_tool" <?= ($cap['capability_scope'] ?? '') === 'external_tool' ? 'selected' : '' ?>>External Tool (⚙️)</option>
                                                                            <option value="identifyshell_specific" <?= ($cap['capability_scope'] ?? '') === 'identifyshell_specific' ? 'selected' : '' ?>>IdentifyShell Specific (🐚)</option>
                                                                        </select>
                                                                    </div>
                                                                    <div class="col-md-3">
                                                                        <div class="form-check mt-4">
                                                                            <input class="form-check-input" type="checkbox" name="is_generic" id="genCheck<?= (int)$cap['id'] ?>" <?= !empty($cap['is_generic']) ? 'checked' : '' ?>>
                                                                            <label class="form-check-label fw-semibold" for="genCheck<?= (int)$cap['id'] ?>">
                                                                                Generic Method
                                                                            </label>
                                                                        </div>
                                                                    </div>
                                                                    <div class="col-md-3">
                                                                        <div class="form-check mt-4">
                                                                            <input class="form-check-input" type="checkbox" name="is_enabled" id="enCheck<?= (int)$cap['id'] ?>" <?= !empty($cap['is_enabled']) ? 'checked' : '' ?>>
                                                                            <label class="form-check-label fw-semibold" for="enCheck<?= (int)$cap['id'] ?>">
                                                                                Enabled
                                                                            </label>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                            <div class="modal-footer">
                                                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                                                <button type="submit" class="btn btn-primary">Save Changes</button>
                                                            </div>
                                                        </form>
                                                    </div>
                                                </div>
                                            </div>

                                            <!-- Add Implementation Modal -->
                                            <div class="modal fade" id="addImplModal<?= (int)$cap['id'] ?>" tabindex="-1">
                                                <div class="modal-dialog modal-lg">
                                                    <div class="modal-content">
                                                        <form method="post" action="capabilities.php<?= $pageQuery ?>">
                                                            <input type="hidden" name="action" value="add_implementation">
                                                            <input type="hidden" name="capability_id" value="<?= (int)$cap['id'] ?>">
                                                            <div class="modal-header">
                                                                <h5 class="modal-title">Bind Implementation Adapter to <?= h($cap['display_name']) ?></h5>
                                                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                                            </div>
                                                            <div class="modal-body">
                                                                <div class="row g-3">
                                                                    <div class="col-md-6">
                                                                        <label class="form-label fw-semibold">Implementation Key</label>
                                                                        <input type="text" name="implementation_key" class="form-control font-monospace" placeholder="e.g. bioclip_adapter_v1" required>
                                                                    </div>
                                                                    <div class="col-md-6">
                                                                        <label class="form-label fw-semibold">Display Name</label>
                                                                        <input type="text" name="display_name" class="form-control" placeholder="e.g. BioCLIP PyTorch Adapter" required>
                                                                    </div>
                                                                    <div class="col-md-6">
                                                                        <label class="form-label fw-semibold">Provider</label>
                                                                        <input type="text" name="provider" class="form-control" placeholder="e.g. open_bioclip" value="core_engine" required>
                                                                    </div>
                                                                    <div class="col-md-6">
                                                                        <label class="form-label fw-semibold">Adapter Module Path</label>
                                                                        <input type="text" name="adapter_module" class="form-control font-monospace" placeholder="e.g. src.adapters.bioclip">
                                                                    </div>
                                                                    <div class="col-md-4">
                                                                        <label class="form-label fw-semibold">Backend Environment</label>
                                                                        <input type="text" name="backend_environment" class="form-control" value="local_host" required>
                                                                    </div>
                                                                    <div class="col-md-4">
                                                                        <label class="form-label fw-semibold">Deployment Scope</label>
                                                                        <select name="implementation_scope" class="form-select">
                                                                            <option value="generic_core">Generic Core</option>
                                                                            <option value="official_extension">Official Extension</option>
                                                                            <option value="external_tool">External Tool</option>
                                                                            <option value="identifyshell_specific">IdentifyShell Specific</option>
                                                                        </select>
                                                                    </div>
                                                                    <div class="col-md-4">
                                                                        <label class="form-label fw-semibold">Availability</label>
                                                                        <select name="availability" class="form-select">
                                                                            <option value="installed">installed</option>
                                                                            <option value="not_installed">not_installed</option>
                                                                            <option value="external">external</option>
                                                                        </select>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                            <div class="modal-footer">
                                                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                                                <button type="submit" class="btn btn-primary">Bind Adapter</button>
                                                            </div>
                                                        </form>
                                                    </div>
                                                </div>
                                            </div>

                                            <!-- Edit Implementation Modals -->
                                            <?php foreach ($impls as $im): ?>
                                                <div class="modal fade" id="editImplModal<?= (int)$im['id'] ?>" tabindex="-1">
                                                    <div class="modal-dialog modal-lg">
                                                        <div class="modal-content">
                                                            <form method="post" action="capabilities.php<?= $pageQuery ?>">
                                                                <input type="hidden" name="action" value="update_implementation">
                                                                <input type="hidden" name="implementation_id" value="<?= (int)$im['id'] ?>">
                                                                <div class="modal-header">
                                                                    <h5 class="modal-title">Edit Adapter: <?= h($im['implementation_key']) ?></h5>
                                                                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                                                </div>
                                                                <div class="modal-body">
                                                                    <div class="row g-3">
                                                                        <div class="col-md-6">
                                                                            <label class="form-label fw-semibold">Display Name</label>
                                                                            <input type="text" name="display_name" class="form-control" value="<?= h($im['display_name']) ?>" required>
                                                                        </div>
                                                                        <div class="col-md-6">
                                                                            <label class="form-label fw-semibold">Provider</label>
                                                                            <input type="text" name="provider" class="form-control" value="<?= h($im['provider']) ?>" required>
                                                                        </div>
                                                                        <div class="col-md-6">
                                                                            <label class="form-label fw-semibold">Adapter Module</label>
                                                                            <input type="text" name="adapter_module" class="form-control font-monospace" value="<?= h($im['adapter_module'] ?? '') ?>">
                                                                        </div>
                                                                        <div class="col-md-6">
                                                                            <label class="form-label fw-semibold">Backend Environment</label>
                                                                            <input type="text" name="backend_environment" class="form-control" value="<?= h($im['backend_environment']) ?>">
                                                                        </div>
                                                                        <div class="col-md-4">
                                                                            <label class="form-label fw-semibold">Deployment Scope</label>
                                                                            <select name="implementation_scope" class="form-select">
                                                                                <option value="generic_core" <?= ($im['implementation_scope'] ?? '') === 'generic_core' ? 'selected' : '' ?>>Generic Core</option>
                                                                                <option value="official_extension" <?= ($im['implementation_scope'] ?? '') === 'official_extension' ? 'selected' : '' ?>>Official Extension</option>
                                                                                <option value="external_tool" <?= ($im['implementation_scope'] ?? '') === 'external_tool' ? 'selected' : '' ?>>External Tool</option>
                                                                                <option value="identifyshell_specific" <?= ($im['implementation_scope'] ?? '') === 'identifyshell_specific' ? 'selected' : '' ?>>IdentifyShell Specific</option>
                                                                            </select>
                                                                        </div>
                                                                        <div class="col-md-4">
                                                                            <label class="form-label fw-semibold">Availability</label>
                                                                            <select name="availability" class="form-select">
                                                                                <option value="installed" <?= ($im['availability'] ?? '') === 'installed' ? 'selected' : '' ?>>installed</option>
                                                                                <option value="not_installed" <?= ($im['availability'] ?? '') === 'not_installed' ? 'selected' : '' ?>>not_installed</option>
                                                                                <option value="external" <?= ($im['availability'] ?? '') === 'external' ? 'selected' : '' ?>>external</option>
                                                                            </select>
                                                                        </div>
                                                                        <div class="col-md-4">
                                                                            <label class="form-label fw-semibold">Validation Status</label>
                                                                            <select name="validation_status" class="form-select">
                                                                                <option value="known" <?= ($im['validation_status'] ?? '') === 'known' ? 'selected' : '' ?>>known</option>
                                                                                <option value="implemented" <?= ($im['validation_status'] ?? '') === 'implemented' ? 'selected' : '' ?>>implemented</option>
                                                                                <option value="validated" <?= ($im['validation_status'] ?? '') === 'validated' ? 'selected' : '' ?>>validated</option>
                                                                            </select>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                                <div class="modal-footer">
                                                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                                                    <button type="submit" class="btn btn-primary">Save Changes</button>
                                                                </div>
                                                            </form>
                                                        </div>
                                                    </div>
                                                </div>
                                            <?php endforeach; ?>

                                        <?php endforeach; ?>
                                    </div>
                                <?php endif; ?>
                            </div>
                        </div>

                        <!-- Edit Application Modal -->
                        <div class="modal fade" id="editAppModal<?= (int)$app['id'] ?>" tabindex="-1">
                            <div class="modal-dialog modal-lg">
                                <div class="modal-content">
                                    <form method="post" action="capabilities.php<?= $pageQuery ?>">
                                        <input type="hidden" name="action" value="update_application">
                                        <input type="hidden" name="application_id" value="<?= (int)$app['id'] ?>">
                                        <div class="modal-header">
                                            <h5 class="modal-title">Edit Application: <?= h($app['display_name']) ?></h5>
                                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                        </div>
                                        <div class="modal-body">
                                            <div class="row g-3">
                                                <div class="col-md-6">
                                                    <label class="form-label fw-semibold">Display Name</label>
                                                    <input type="text" name="display_name" class="form-control" value="<?= h($app['display_name']) ?>" required>
                                                </div>
                                                <div class="col-md-6">
                                                    <label class="form-label fw-semibold">Category</label>
                                                    <select name="category" class="form-select">
                                                        <option value="identifyshell_specific" <?= $app['category'] === 'identifyshell_specific' ? 'selected' : '' ?>>🐚 IdentifyShell Specific</option>
                                                        <option value="vision_ml" <?= $app['category'] === 'vision_ml' ? 'selected' : '' ?>>Vision &amp; Deep Learning</option>
                                                        <option value="taxonomy" <?= $app['category'] === 'taxonomy' ? 'selected' : '' ?>>Taxonomy &amp; Nomenclature</option>
                                                        <option value="statistics" <?= $app['category'] === 'statistics' ? 'selected' : '' ?>>Morphometrics &amp; Statistics</option>
                                                        <option value="dataset" <?= $app['category'] === 'dataset' ? 'selected' : '' ?>>Dataset Governance</option>
                                                        <option value="molecular" <?= $app['category'] === 'molecular' ? 'selected' : '' ?>>Molecular &amp; Genetics</option>
                                                    </select>
                                                </div>
                                                <div class="col-md-6">
                                                    <label class="form-label fw-semibold">Host Environment</label>
                                                    <input type="text" name="host_environment" class="form-control" value="<?= h($app['host_environment']) ?>" required>
                                                </div>
                                                <div class="col-md-6">
                                                    <label class="form-label fw-semibold">Invocation Mechanism</label>
                                                    <select name="invocation_type" class="form-select">
                                                        <option value="manual_web_ui" <?= $app['invocation_type'] === 'manual_web_ui' ? 'selected' : '' ?>>Manual / Web Dashboard</option>
                                                        <option value="cli_script" <?= $app['invocation_type'] === 'cli_script' ? 'selected' : '' ?>>CLI Script</option>
                                                        <option value="python_function" <?= $app['invocation_type'] === 'python_function' ? 'selected' : '' ?>>Python Module / Function</option>
                                                        <option value="rest_api" <?= $app['invocation_type'] === 'rest_api' ? 'selected' : '' ?>>External / Local REST API</option>
                                                    </select>
                                                </div>
                                                <div class="col-12">
                                                    <label class="form-label fw-semibold">Interface / Documentation URL</label>
                                                    <input type="url" name="interface_url" class="form-control font-monospace" value="<?= h($app['interface_url'] ?? '') ?>">
                                                </div>
                                                <div class="col-12">
                                                    <label class="form-label fw-semibold">Description</label>
                                                    <textarea name="description" class="form-control" rows="3"><?= h($app['description']) ?></textarea>
                                                </div>
                                                <div class="col-md-6">
                                                    <div class="form-check mt-2">
                                                        <input class="form-check-input" type="checkbox" name="is_gpu_required" id="editGpuReq<?= (int)$app['id'] ?>" <?= !empty($app['is_gpu_required']) ? 'checked' : '' ?>>
                                                        <label class="form-check-label fw-semibold" for="editGpuReq<?= (int)$app['id'] ?>">
                                                            Requires Dedicated GPU (CUDA)
                                                        </label>
                                                    </div>
                                                </div>
                                                <div class="col-md-6">
                                                    <div class="form-check mt-2">
                                                        <input class="form-check-input" type="checkbox" name="is_enabled" id="editEnApp<?= (int)$app['id'] ?>" <?= !empty($app['is_enabled']) ? 'checked' : '' ?>>
                                                        <label class="form-check-label fw-semibold" for="editEnApp<?= (int)$app['id'] ?>">
                                                            Enabled in Registry
                                                        </label>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="modal-footer">
                                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                            <button type="submit" class="btn btn-primary">Save Changes</button>
                                        </div>
                                    </form>
                                </div>
                            </div>
                        </div>

                        <!-- Add Capability Modal for App -->
                        <div class="modal fade" id="addCapModal<?= (int)$app['id'] ?>" tabindex="-1">
                            <div class="modal-dialog modal-lg">
                                <div class="modal-content">
                                    <form method="post" action="capabilities.php<?= $pageQuery ?>">
                                        <input type="hidden" name="action" value="add_capability">
                                        <input type="hidden" name="application_id" value="<?= (int)$app['id'] ?>">
                                        <div class="modal-header">
                                            <h5 class="modal-title">Add Capability to <?= h($app['display_name']) ?></h5>
                                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                        </div>
                                        <div class="modal-body">
                                            <div class="row g-3">
                                                <div class="col-md-6">
                                                    <label class="form-label fw-semibold">Capability Key (Identifier)</label>
                                                    <input type="text" name="capability_key" class="form-control font-monospace" placeholder="e.g. extract_morphometrics_features" required>
                                                </div>
                                                <div class="col-md-6">
                                                    <label class="form-label fw-semibold">Display Name</label>
                                                    <input type="text" name="display_name" class="form-control" placeholder="e.g. Extract Morphometric Contour Features" required>
                                                </div>
                                                <div class="col-md-6">
                                                    <label class="form-label fw-semibold">Standardized Biodiversity Domain</label>
                                                    <select name="domain" class="form-select">
                                                        <?php foreach ($domains as $d): ?>
                                                            <option value="<?= h($d['domain']) ?>">
                                                                <?= h($d['display_name']) ?>
                                                            </option>
                                                        <?php endforeach; ?>
                                                    </select>
                                                </div>
                                                <div class="col-md-6">
                                                    <label class="form-label fw-semibold">Scientific Tasks</label>
                                                    <input type="text" name="scientific_tasks" class="form-control" placeholder="e.g. Landmark registration, morphological disparity">
                                                </div>
                                                <div class="col-12">
                                                    <label class="form-label fw-semibold">Scientific Purpose</label>
                                                    <textarea name="scientific_purpose" class="form-control" rows="2" placeholder="What biological evidence or computational step does this achieve?" required></textarea>
                                                </div>
                                                <div class="col-md-3">
                                                    <label class="form-label fw-semibold">Typical Duration</label>
                                                    <input type="text" name="typical_duration" class="form-control" placeholder="e.g. 5–15 minutes" value="5–15 minutes">
                                                </div>
                                                <div class="col-md-3">
                                                    <label class="form-label fw-semibold">Reproducibility</label>
                                                    <select name="reproducibility_level" class="form-select">
                                                        <option value="deterministic">Deterministic</option>
                                                        <option value="stochastic_with_seed">Stochastic (with Seed)</option>
                                                        <option value="dynamic_external">Dynamic External</option>
                                                    </select>
                                                </div>
                                                <div class="col-md-6">
                                                    <div class="form-check mt-4">
                                                        <input class="form-check-input" type="checkbox" name="is_generic" id="genCheckNew<?= (int)$app['id'] ?>" checked>
                                                        <label class="form-check-label fw-semibold" for="genCheckNew<?= (int)$app['id'] ?>">
                                                            Generic Scientific Method
                                                        </label>
                                                    </div>
                                                </div>
                                                <div class="col-12">
                                                    <label class="form-label fw-semibold">Default Parameters (JSON)</label>
                                                    <textarea name="default_parameters" class="form-control font-monospace" rows="2">{"batch_size": 32, "seed": 42}</textarea>
                                                </div>
                                                <div class="col-12">
                                                    <div class="form-check">
                                                        <input class="form-check-input" type="checkbox" name="modifies_data" id="modData<?= (int)$app['id'] ?>">
                                                        <label class="form-check-label" for="modData<?= (int)$app['id'] ?>">
                                                            Mutates / Creates Dataset Version (Check only if this capability writes derived datasets)
                                                        </label>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="modal-footer">
                                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                            <button type="submit" class="btn btn-primary">Save Capability</button>
                                        </div>
                                    </form>
                                </div>
                            </div>
                        </div>
                    <?php endforeach; ?>
                </div>
            <?php endif; ?>

        </main>
    </div>
</div>

<!-- Register Application Modal -->
<div class="modal fade" id="registerAppModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <form method="post" action="capabilities.php<?= $pageQuery ?>">
                <input type="hidden" name="action" value="create_application">
                <div class="modal-header">
                    <h5 class="modal-title">Register Scientific Application / Tool</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="row g-3">
                        <div class="col-md-6">
                            <label class="form-label fw-semibold">Application Identifier</label>
                            <input type="text" name="name" class="form-control font-monospace" placeholder="e.g. bio_clip_feature_extractor" required>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label fw-semibold">Display Name</label>
                            <input type="text" name="display_name" class="form-control" placeholder="e.g. BioCLIP Specimen Feature Extractor" required>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label fw-semibold">Category</label>
                            <select name="category" class="form-select">
                                <option value="identifyshell_specific">🐚 IdentifyShell Specific</option>
                                <option value="vision_ml" selected>Vision &amp; Deep Learning</option>
                                <option value="taxonomy">Taxonomy &amp; Nomenclature</option>
                                <option value="statistics">Morphometrics &amp; Statistics</option>
                                <option value="dataset">Dataset Governance</option>
                                <option value="molecular">Molecular &amp; Genetics</option>
                            </select>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label fw-semibold">Invocation Mechanism</label>
                            <select name="invocation_type" class="form-select">
                                <option value="manual_web_ui">Manual / Web Dashboard</option>
                                <option value="cli_script">CLI Script</option>
                                <option value="python_function">Python Module / Function</option>
                                <option value="rest_api">External / Local REST API</option>
                            </select>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label fw-semibold">Host Environment</label>
                            <input type="text" name="host_environment" class="form-control" placeholder="e.g. Local GPU Node / Compute Cluster" required>
                        </div>
                        <div class="col-12">
                            <label class="form-label fw-semibold">Interface / Documentation URL</label>
                            <input type="url" name="interface_url" class="form-control font-monospace" placeholder="e.g. http://localhost:8080/pipeline/index.php">
                        </div>
                        <div class="col-12">
                            <label class="form-label fw-semibold">Description</label>
                            <textarea name="description" class="form-control" rows="3" placeholder="What scientific role does this application play in the research ecosystem?" required></textarea>
                        </div>
                        <div class="col-md-6">
                            <div class="form-check mt-2">
                                <input class="form-check-input" type="checkbox" name="is_gpu_required" id="gpuReqNew">
                                <label class="form-check-label fw-semibold" for="gpuReqNew">
                                    Requires Dedicated GPU (CUDA)
                                </label>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn btn-primary">Register Application</button>
                </div>
            </form>
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>

