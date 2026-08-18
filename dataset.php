<?php

declare(strict_types=1);

require_once __DIR__ . '/includes/api.php';
require_once __DIR__ . '/includes/functions.php';


$projectId = 0;
$project = null;
$datasets = [];
$error = null;

$noticeKey = null;

try {
    $projectId = getRequiredPositiveInt('project_id');

    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        $action = trim($_POST['action'] ?? '');
        if ($action === 'register_dataset') {
            $versionKey = trim($_POST['version_key'] ?? '');
            $sourceSystem = trim($_POST['source_system'] ?? '');
            $memberCountRaw = trim($_POST['member_count'] ?? '');
            $manifestUri = trim($_POST['manifest_uri'] ?? '');
            $manifestSha = trim($_POST['manifest_sha256'] ?? '');
            $selectionRaw = trim($_POST['selection_definition'] ?? '');
            $groupingRaw = trim($_POST['grouping_keys'] ?? '');

            if ($versionKey === '') {
                throw new InvalidArgumentException('Version key is required.');
            }
            if ($sourceSystem === '') {
                throw new InvalidArgumentException('Source system is required.');
            }

            $payload = [
                'version_key' => $versionKey,
                'source_system' => $sourceSystem,
                'member_count' => $memberCountRaw !== '' ? (int)$memberCountRaw : null,
                'manifest_uri' => $manifestUri !== '' ? $manifestUri : null,
                'manifest_sha256' => $manifestSha !== '' ? $manifestSha : null,
                'selection_definition' => $selectionRaw !== '' ? json_decode($selectionRaw, true) : null,
                'grouping_keys' => $groupingRaw !== '' ? json_decode($groupingRaw, true) : null,
            ];

            api_post('/projects/' . $projectId . '/datasets', $payload);
            header('Location: dataset.php?project_id=' . $projectId . '&dataset_registered=1');
            exit;
        }
    }

    $project = api_get('/projects/' . $projectId);
    $datasets = api_get('/projects/' . $projectId . '/datasets');

} catch (Throwable $e) {
    $error = $e->getMessage();
}

if (isset($_GET['dataset_registered'])) {
    $noticeKey = 'Dataset version registered and frozen successfully!';
}


$activePage = 'dataset';

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
        Dataset Versions - Biodiversity AI Scientist
    </title>

    <link
        href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css"
        rel="stylesheet"
    >

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
                Unable to load datasets
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
            <?php if (!empty($noticeKey)): ?>
                <div class="alert alert-success alert-dismissible fade show mb-4" role="alert">
                    <?= h($noticeKey) ?>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            <?php endif; ?>


            <div class="d-flex
                        justify-content-between
                        align-items-start
                        mb-4">

                <div>

                    <h2 class="h3 mb-1">
                        Dataset Versions
                    </h2>

                    <p class="text-muted mb-0">

                        Versioned analytical populations used
                        for reproducible scientific analyses.

                    </p>

                </div>

                <div class="d-flex align-items-center gap-2">
                    <span class="badge bg-light text-dark border fs-6">
                        <?= count($datasets) ?> dataset<?= count($datasets) === 1 ? '' : 's' ?>
                    </span>
                    <button type="button" class="btn btn-primary btn-sm fw-semibold shadow-sm" data-bs-toggle="modal" data-bs-target="#registerDatasetModal">
                        + Register Dataset Version
                    </button>
                </div>

            </div>


            <div class="alert alert-info">

                A DatasetVersion identifies the exact analytical
                population used by an analysis. Dataset membership,
                grouping structure and integrity information should
                remain reproducible after the dataset has been registered.

            </div>


            <?php if (count($datasets) === 0): ?>


                <div class="card shadow-sm">

                    <div class="card-body text-center py-5">

                        <h3 class="h5">
                            No dataset versions
                        </h3>

                        <p class="text-muted mb-3">
                            No analytical dataset has yet been registered for this project.
                        </p>
                        <button type="button" class="btn btn-primary btn-sm fw-semibold shadow-sm" data-bs-toggle="modal" data-bs-target="#registerDatasetModal">
                            + Register Dataset Version
                        </button>

                    </div>

                </div>


            <?php else: ?>


                <?php foreach ($datasets as $dataset): ?>


                    <div class="card shadow-sm mb-4">

                        <div class="card-header bg-white">

                            <div class="d-flex
                                        justify-content-between
                                        align-items-center">

                                <div>

                                    <strong>
                                        <?= h($dataset['version_key']) ?>
                                    </strong>

                                </div>

                                <span class="badge bg-secondary">

                                    Dataset
                                    #<?= (int)$dataset['id'] ?>

                                </span>

                            </div>

                        </div>


                        <div class="card-body">


                            <div class="row g-4">


                                <div class="col-lg-6">

                                    <table class="table table-sm mb-0">

                                        <tbody>

                                        <tr>
                                            <th style="width: 40%;">
                                                Source system
                                            </th>
                                            <td>
                                                <?= h($dataset['source_system']) ?>
                                            </td>
                                        </tr>

                                        <tr>
                                            <th>
                                                Members
                                            </th>
                                            <td>
                                                <?php
                                                if ($dataset['member_count'] === null) {
                                                    echo '<span class="text-muted">Unknown</span>';
                                                } else {
                                                    echo number_format(
                                                        (int)$dataset['member_count']
                                                    );
                                                }
                                                ?>
                                            </td>
                                        </tr>

                                        <tr>
                                            <th>
                                                Created
                                            </th>
                                            <td>
                                                <?php
                                                $created = new DateTime(
                                                    $dataset['created_at']
                                                );

                                                echo h(
                                                    $created->format(
                                                        'Y-m-d H:i:s'
                                                    )
                                                );
                                                ?>
                                            </td>
                                        </tr>

                                        <tr>
                                            <th>
                                                Manifest
                                            </th>
                                            <td>
                                                <?php if (!empty($dataset['manifest_uri'])): ?>

                                                    <code>
                                                        <?= h($dataset['manifest_uri']) ?>
                                                    </code>

                                                <?php else: ?>

                                                    <span class="text-muted">
                                                        Not registered
                                                    </span>

                                                <?php endif; ?>
                                            </td>
                                        </tr>

                                        <tr>
                                            <th>
                                                SHA-256
                                            </th>
                                            <td>
                                                <?php if (!empty($dataset['manifest_sha256'])): ?>

                                                    <code class="small">
                                                        <?= h($dataset['manifest_sha256']) ?>
                                                    </code>

                                                <?php else: ?>

                                                    <span class="text-muted">
                                                        Not registered
                                                    </span>

                                                <?php endif; ?>
                                            </td>
                                        </tr>

                                        </tbody>

                                    </table>

                                </div>


                                <div class="col-lg-6">

                                    <div class="small
                                                text-uppercase
                                                text-muted
                                                fw-semibold
                                                mb-2">

                                        Grouping keys

                                    </div>

                                    <?php
                                    $groupingKeys =
                                        $dataset['grouping_keys'] ?? [];
                                    ?>

                                    <?php if (count($groupingKeys) === 0): ?>

                                        <p class="text-muted">
                                            No grouping keys registered.
                                        </p>

                                    <?php else: ?>

                                        <div class="mb-4">

                                            <?php foreach ($groupingKeys as $key): ?>

                                                <span class="badge
                                                             bg-light
                                                             text-dark
                                                             border
                                                             me-1
                                                             mb-1">

                                                    <?= h((string)$key) ?>

                                                </span>

                                            <?php endforeach; ?>

                                        </div>

                                    <?php endif; ?>


                                    <div class="small
                                                text-uppercase
                                                text-muted
                                                fw-semibold
                                                mb-2">

                                        Selection definition

                                    </div>

                                    <?php
                                    $selection =
                                        $dataset['selection_definition'];
                                    ?>

                                    <?php if ($selection === null): ?>

                                        <p class="text-muted mb-0">
                                            No selection definition registered.
                                        </p>

                                    <?php else: ?>

                                        <pre class="bg-light border rounded p-3 mb-0"><code><?= h(
                                            json_encode(
                                                $selection,
                                                JSON_PRETTY_PRINT |
                                                JSON_UNESCAPED_SLASHES
                                            )
                                        ) ?></code></pre>

                                    <?php endif; ?>

                                </div>


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



<!-- Register Dataset Version Modal -->
<div class="modal fade" id="registerDatasetModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <form method="post" action="dataset.php?project_id=<?= $projectId ?>">
                <input type="hidden" name="action" value="register_dataset">
                <input type="hidden" name="project_id" value="<?= $projectId ?>">

                <div class="modal-header bg-primary text-white">
                    <h5 class="modal-title">Register &amp; Freeze Dataset Version</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <p class="small text-muted mb-3">
                        Define an immutable, versioned population for reproducible analytical execution.
                    </p>

                    <div class="row g-3">
                        <div class="col-md-6">
                            <label class="form-label fw-semibold">Version Key <span class="text-danger">*</span></label>
                            <input type="text" name="version_key" class="form-control" placeholder="e.g. nassarius_studio_v1" required>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label fw-semibold">Source System <span class="text-danger">*</span></label>
                            <input type="text" name="source_system" class="form-control" placeholder="e.g. DWH.OccurrenceImages" value="DWH" required>
                        </div>

                        <div class="col-md-6">
                            <label class="form-label fw-semibold">Member Count</label>
                            <input type="number" name="member_count" class="form-control" placeholder="e.g. 1240" min="0">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label fw-semibold">Manifest URI</label>
                            <input type="text" name="manifest_uri" class="form-control" placeholder="e.g. dwh://datasets/nassarius_studio_v1.parquet">
                        </div>

                        <div class="col-12">
                            <label class="form-label fw-semibold">Selection Definition (JSON)</label>
                            <textarea name="selection_definition" class="form-control font-monospace small" rows="3" placeholder='{"genus": "Nassarius", "domain": "studio", "min_images_per_species": 15}'></textarea>
                            <div class="form-text">JSON object specifying filters, taxa, and data inclusion criteria.</div>
                        </div>

                        <div class="col-12">
                            <label class="form-label fw-semibold">Grouping Keys (JSON Array)</label>
                            <input type="text" name="grouping_keys" class="form-control font-monospace small" placeholder='["species_id", "source_institution"]'>
                            <div class="form-text">Stratification or grouping dimensions used for source-aware splits.</div>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn btn-primary">Freeze &amp; Register Dataset</button>
                </div>
            </form>
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js"></script>

</body>
</html>
