<?php

declare(strict_types=1);

require_once __DIR__ . '/includes/api.php';
require_once __DIR__ . '/includes/functions.php';

$status = null;
$diagnostic = null;
$error = null;
$flashSuccess = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = trim($_POST['action'] ?? '');
    try {
        if ($action === 'save_llm_config') {
            $provider = trim($_POST['provider'] ?? 'openai_responses');
            $baseUrl = trim($_POST['base_url'] ?? 'https://api.openai.com/v1');
            $apiKey = trim($_POST['api_key'] ?? '');
            $defaultModel = trim($_POST['default_model'] ?? 'gpt-4o');
            $allowedModels = trim($_POST['allowed_models'] ?? $defaultModel);

            $saveRes = api_post('/config/llm', [
                'enabled' => true,
                'provider' => $provider,
                'base_url' => $baseUrl,
                'api_key' => $apiKey !== '' ? $apiKey : null,
                'default_model' => $defaultModel,
                'allowed_models' => $allowedModels,
            ]);

            $flashSuccess = 'LLM Gateway configuration updated successfully in .env!';
            // Test connection automatically
            try {
                $diagnostic = api_post_empty('/llm-gateway/test-connection');
            } catch (Throwable $e) {
                $error = 'Saved, but connection test failed: ' . $e->getMessage();
            }
        } elseif ($action === 'test_connection') {
            $diagnostic = api_post_empty('/llm-gateway/test-connection');
        }
    } catch (Throwable $e) {
        $error = $e->getMessage();
    }
}

try {
    $status = api_get('/llm-gateway/status');
} catch (Throwable $e) {
    if ($error === null) {
        $error = $e->getMessage();
    }
}

?>
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Configuration - Biodiversity AI Scientist</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
    <link href="css/app.css" rel="stylesheet">
</head>
<body class="bg-light">

<?php require_once __DIR__ . '/includes/navbar.php'; ?>

<main class="container py-4">
    <div class="mb-4">
        <h1 class="h3 mb-1"><i class="bi bi-gear-wide-connected text-primary me-2"></i>LLM Gateway Configuration</h1>
        <p class="text-muted mb-0">Configure your LLM provider credentials, default models, and test live connection authentication.</p>
    </div>

    <?php if ($flashSuccess !== null): ?>
        <div class="alert alert-success alert-dismissible fade show shadow-sm" role="alert">
            <i class="bi bi-check-circle-fill me-2"></i><?= h($flashSuccess) ?>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    <?php endif; ?>

    <?php if ($error !== null): ?>
        <div class="alert alert-danger alert-dismissible fade show shadow-sm" role="alert">
            <i class="bi bi-exclamation-triangle-fill me-2"></i><strong>Error:</strong> <?= h($error) ?>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    <?php endif; ?>

    <div class="row g-4">
        <!-- Live Status Card -->
        <div class="col-lg-5">
            <?php if ($status !== null): ?>
                <div class="card shadow-sm border-0 h-100 bg-white">
                    <div class="card-header bg-light py-3 border-0 fw-semibold d-flex justify-content-between align-items-center">
                        <span><i class="bi bi-cpu text-primary me-2"></i>Active Gateway Status</span>
                        <span class="badge <?= $status['configured'] ? 'bg-success' : 'bg-warning text-dark' ?>">
                            <?= $status['configured'] ? 'Configured & Active' : 'API Key Required' ?>
                        </span>
                    </div>
                    <div class="card-body">
                        <dl class="row mb-0 small">
                            <dt class="col-sm-4 text-muted">Gateway</dt>
                            <dd class="col-sm-8 fw-semibold"><?= $status['configured'] ? '<span class="text-success"><i class="bi bi-check-circle me-1"></i>Ready</span>' : '<span class="text-warning"><i class="bi bi-exclamation-circle me-1"></i>Unconfigured</span>' ?></dd>

                            <dt class="col-sm-4 text-muted">Provider</dt>
                            <dd class="col-sm-8 font-monospace"><code><?= h($status['provider']) ?></code></dd>

                            <dt class="col-sm-4 text-muted">Default Model</dt>
                            <dd class="col-sm-8 fw-semibold"><?= h($status['default_model'] ?? 'Not set') ?></dd>

                            <dt class="col-sm-4 text-muted">API Key</dt>
                            <dd class="col-sm-8"><?= $status['api_key_configured'] ? '<span class="badge bg-success-subtle text-success">Saved Securely</span>' : '<span class="badge bg-danger-subtle text-danger">Not Configured</span>' ?></dd>

                            <dt class="col-sm-4 text-muted">Allowed Models</dt>
                            <dd class="col-sm-8"><?= (int)$status['allowed_model_count'] ?> model(s)</dd>
                        </dl>

                        <?php if ($diagnostic !== null): ?>
                            <div class="mt-4 pt-3 border-top">
                                <h6 class="fw-bold text-success mb-2"><i class="bi bi-patch-check-fill me-1"></i>Connection Test Passed</h6>
                                <dl class="row mb-0 small">
                                    <dt class="col-sm-5 text-muted">Authenticated</dt>
                                    <dd class="col-sm-7 fw-semibold"><?= $diagnostic['authenticated'] ? 'Yes (Valid Key)' : 'No' ?></dd>
                                    <dt class="col-sm-5 text-muted">Quota Status</dt>
                                    <dd class="col-sm-7"><span class="badge <?= $diagnostic['quota_available'] ? 'bg-success' : 'bg-danger' ?>"><?= $diagnostic['quota_available'] ? 'Available' : 'Exhausted' ?></span></dd>
                                </dl>
                            </div>
                        <?php endif; ?>
                    </div>
                    <div class="card-footer bg-white border-top py-2 text-end">
                        <form method="post" class="d-inline">
                            <input type="hidden" name="action" value="test_connection">
                            <button class="btn btn-outline-primary btn-sm" type="submit" <?= !$status['configured'] ? 'disabled' : '' ?>>
                                <i class="bi bi-arrow-repeat me-1"></i>Test Connection
                            </button>
                        </form>
                    </div>
                </div>
            <?php endif; ?>
        </div>

        <!-- Interactive Setup Form Card -->
        <div class="col-lg-7">
            <div class="card shadow-sm border-0 bg-white">
                <div class="card-header bg-light py-3 border-0 fw-semibold">
                    <i class="bi bi-sliders text-primary me-2"></i>Configure Provider Credentials &amp; Models
                </div>
                <div class="card-body">
                    <form method="post" id="formLlmConfig">
                        <input type="hidden" name="action" value="save_llm_config">

                        <div class="mb-3">
                            <label class="form-label small fw-semibold text-muted mb-1">Provider Preset</label>
                            <select id="selectProviderPreset" class="form-select form-select-sm" onchange="applyProviderPreset(this.value);">
                                <option value="openai">OpenAI (GPT-4o, GPT-4o-mini)</option>
                                <option value="deepseek">DeepSeek (deepseek-chat, deepseek-coder)</option>
                                <option value="ollama">Local Ollama (Offline / Free: llama3.1, qwen2.5)</option>
                                <option value="custom">Custom Compatible Endpoint</option>
                            </select>
                        </div>

                        <input type="hidden" id="inputProvider" name="provider" value="openai_responses">

                        <div class="mb-3">
                            <label class="form-label small fw-semibold text-muted mb-1">API Base URL</label>
                            <input type="url" id="inputBaseUrl" name="base_url" class="form-control form-control-sm font-monospace" value="https://api.openai.com/v1" required>
                        </div>

                        <div class="mb-3">
                            <label class="form-label small fw-semibold text-muted mb-1">API Key</label>
                            <div class="input-group input-group-sm">
                                <input type="password" id="inputApiKey" name="api_key" class="form-control font-monospace" placeholder="Paste your API key (e.g. sk-...)">
                                <button class="btn btn-outline-secondary" type="button" onclick="togglePasswordVisibility();" title="Toggle visibility">
                                    <i class="bi bi-eye" id="toggleIcon"></i>
                                </button>
                            </div>
                            <div class="form-text small">Leave blank to keep existing server key. For local Ollama, leave blank.</div>
                        </div>

                        <div class="row g-2 mb-3">
                            <div class="col-md-6">
                                <label class="form-label small fw-semibold text-muted mb-1">Default Model Name</label>
                                <input type="text" id="inputDefaultModel" name="default_model" class="form-control form-control-sm font-monospace" value="gpt-4o" required>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label small fw-semibold text-muted mb-1">Allowed Models (Comma-separated)</label>
                                <input type="text" id="inputAllowedModels" name="allowed_models" class="form-control form-control-sm font-monospace" value="gpt-4o,gpt-4o-mini" required>
                            </div>
                        </div>

                        <div class="d-flex justify-content-between align-items-center mt-4 pt-2 border-top">
                            <small class="text-muted"><i class="bi bi-shield-lock me-1"></i>Keys are saved locally in <code>.env</code></small>
                            <button type="submit" class="btn btn-primary btn-sm px-4 shadow-sm">
                                <i class="bi bi-save me-1"></i>Save &amp; Test Connection
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</main>

<script>
function applyProviderPreset(preset) {
    const providerInput = document.getElementById('inputProvider');
    const baseUrlInput = document.getElementById('inputBaseUrl');
    const defaultModelInput = document.getElementById('inputDefaultModel');
    const allowedModelsInput = document.getElementById('inputAllowedModels');
    const apiKeyInput = document.getElementById('inputApiKey');

    if (preset === 'openai') {
        providerInput.value = 'openai_responses';
        baseUrlInput.value = 'https://api.openai.com/v1';
        defaultModelInput.value = 'gpt-4o';
        allowedModelsInput.value = 'gpt-4o,gpt-4o-mini';
        apiKeyInput.placeholder = 'Paste your OpenAI API key (sk-...)';
    } else if (preset === 'deepseek') {
        providerInput.value = 'deepseek_chat';
        baseUrlInput.value = 'https://api.deepseek.com';
        defaultModelInput.value = 'deepseek-chat';
        allowedModelsInput.value = 'deepseek-chat,deepseek-reasoner';
        apiKeyInput.placeholder = 'Paste your DeepSeek API key (sk-...)';
    } else if (preset === 'ollama') {
        providerInput.value = 'ollama';
        baseUrlInput.value = 'http://localhost:11434/v1';
        defaultModelInput.value = 'llama3.1';
        allowedModelsInput.value = 'llama3.1,qwen2.5,mistral';
        apiKeyInput.value = 'ollama';
        apiKeyInput.placeholder = 'Not required for local Ollama';
    } else if (preset === 'custom') {
        providerInput.value = 'custom';
        apiKeyInput.placeholder = 'Enter API Key if required';
    }
}

function togglePasswordVisibility() {
    const input = document.getElementById('inputApiKey');
    const icon = document.getElementById('toggleIcon');
    if (input.type === 'password') {
        input.type = 'text';
        icon.className = 'bi bi-eye-slash';
    } else {
        input.type = 'password';
        icon.className = 'bi bi-eye';
    }
}
</script>

<?php require_once __DIR__ . '/includes/footer.php'; ?>
