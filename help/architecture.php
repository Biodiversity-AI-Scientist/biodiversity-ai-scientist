<?php

declare(strict_types=1);

$activeTopic = 'architecture';
$pageTitle = 'System Architecture & Infrastructure — AI Scientist Help';

require_once __DIR__ . '/includes/help_header.php';

?>

<div class="row mb-4">
    <div class="col-12">
        <div class="d-flex align-items-center gap-2 mb-1">
            <span class="badge bg-primary text-uppercase tracking-wide">Infrastructure &amp; Control Plane</span>
            <h1 class="h3 mb-0 fw-bold">System Architecture &amp; Data Flow</h1>
        </div>
        <p class="text-muted mb-0">
            Physical tri-node infrastructure, separation of control plane from GPU compute, DWH occurrence data store, and persistent artifact hierarchies.
        </p>
    </div>
</div>

<!-- Architecture SVG Diagram Card -->
<div class="card shadow-sm border-0 mb-4">
    <div class="card-header bg-white py-3 border-bottom d-flex justify-content-between align-items-center">
        <h5 class="card-title fw-bold mb-0 text-dark"><i class="bi bi-diagram-3 text-primary me-2"></i>Physical Nodes &amp; Data Flow Architecture</h5>
        <span class="badge bg-light text-dark border">Tri-Node Production Topology</span>
    </div>
    <div class="card-body p-4">
        <div class="svg-container mb-3">
            <svg width="950" height="420" viewBox="0 0 950 420" xmlns="http://www.w3.org/2000/svg" style="max-width: 100%; height: auto;">
                <defs>
                    <marker id="arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                        <polygon points="0 0, 8 3, 0 6" fill="#475569" />
                    </marker>
                    <marker id="arrow-blue" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                        <polygon points="0 0, 8 3, 0 6" fill="#0d6efd" />
                    </marker>
                    <marker id="arrow-purple" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                        <polygon points="0 0, 8 3, 0 6" fill="#7c3aed" />
                    </marker>
                </defs>

                <!-- 1. Control Plane & Web Server -->
                <rect x="30" y="30" width="280" height="200" rx="10" fill="#f8fafc" stroke="#0d6efd" stroke-width="2.5" />
                <rect x="30" y="30" width="280" height="36" rx="10" fill="#0d6efd" />
                <text x="170" y="54" text-anchor="middle" fill="#ffffff" font-family="sans-serif" font-weight="bold" font-size="14">Control Plane &amp; UI</text>
                <text x="50" y="90" fill="#0f172a" font-family="sans-serif" font-weight="bold" font-size="12">• Apache / PHP 8.3 Workspace UI</text>
                <text x="50" y="112" fill="#0f172a" font-family="sans-serif" font-weight="bold" font-size="12">• FastAPI Backend (Port 8000)</text>
                <text x="50" y="134" fill="#64748b" font-family="sans-serif" font-size="11">  - Scientific Context Service</text>
                <text x="50" y="152" fill="#64748b" font-family="sans-serif" font-size="11">  - Investigation DAG Engine</text>
                <text x="50" y="170" fill="#64748b" font-family="sans-serif" font-size="11">  - Capability Selection Service</text>
                <text x="50" y="188" fill="#64748b" font-family="sans-serif" font-size="11">  - LLM Gateway &amp; JSON Repair Engine</text>
                <text x="50" y="210" fill="#0369a1" font-family="sans-serif" font-weight="bold" font-size="11">• SQLAlchemy ORM + Alembic</text>

                <!-- 2. Data Store & Relational World Model -->
                <rect x="370" y="30" width="240" height="150" rx="10" fill="#f0fdf4" stroke="#16a34a" stroke-width="2.5" />
                <rect x="370" y="30" width="240" height="36" rx="10" fill="#16a34a" />
                <text x="490" y="54" text-anchor="middle" fill="#ffffff" font-family="sans-serif" font-weight="bold" font-size="14">Database &amp; Data Store</text>
                <text x="390" y="90" fill="#0f172a" font-family="sans-serif" font-weight="bold" font-size="12">• GBIF &amp; OBIS Occurrences</text>
                <text x="390" y="112" fill="#0f172a" font-family="sans-serif" font-weight="bold" font-size="12">• Specimen Image Archives</text>
                <text x="390" y="134" fill="#0f172a" font-family="sans-serif" font-weight="bold" font-size="12">• WoRMS Taxonomic Cache</text>
                <text x="390" y="156" fill="#15803d" font-family="sans-serif" font-size="11">• Scientific World Model Tables</text>

                <!-- 3. GPU Worker & Compute Node -->
                <rect x="670" y="30" width="250" height="200" rx="10" fill="#faf5ff" stroke="#7c3aed" stroke-width="2.5" />
                <rect x="670" y="30" width="250" height="36" rx="10" fill="#7c3aed" />
                <text x="795" y="54" text-anchor="middle" fill="#ffffff" font-family="sans-serif" font-weight="bold" font-size="14">Compute &amp; Worker Node</text>
                <text x="690" y="90" fill="#0f172a" font-family="sans-serif" font-weight="bold" font-size="12">• CUDA 12+ Acceleration</text>
                <text x="690" y="112" fill="#0f172a" font-family="sans-serif" font-weight="bold" font-size="12">• DINOv3 Feature Extractor</text>
                <text x="690" y="134" fill="#0f172a" font-family="sans-serif" font-weight="bold" font-size="12">• ResNet Supervised Training</text>
                <text x="690" y="156" fill="#0f172a" font-family="sans-serif" font-weight="bold" font-size="12">• Papermill Notebook Runner</text>
                <text x="690" y="178" fill="#6b21a8" font-family="sans-serif" font-size="11">• Python Scientific Compute Stack</text>

                <!-- 4. Shared Storage / Artifact Tree -->
                <rect x="250" y="300" width="450" height="90" rx="10" fill="#fffbeb" stroke="#d97706" stroke-width="2" />
                <rect x="250" y="300" width="450" height="28" rx="10" fill="#d97706" />
                <text x="475" y="320" text-anchor="middle" fill="#ffffff" font-family="sans-serif" font-weight="bold" font-size="12">Persistent Artifacts &amp; Datasets (`/projects/project_{id}/`)</text>
                <text x="270" y="348" fill="#78350f" font-family="sans-serif" font-size="11">📁 `datasets/` (Occurrence CSV/Parquet, Aperture crops)</text>
                <text x="270" y="366" fill="#78350f" font-family="sans-serif" font-size="11">📁 `embeddings/` (384-dim DINOv3 feature vectors) | 📁 `models/` (ResNet weights, checkpoints)</text>
                <text x="270" y="384" fill="#78350f" font-family="sans-serif" font-size="11">📁 `results/` (Confusion matrices, PCA projections, statistical tests, metrics JSON)</text>

                <!-- Interconnecting Data Flow Arrows -->
                <!-- Control Plane -> Database (SQL) -->
                <line x1="310" y1="105" x2="370" y2="105" stroke="#16a34a" stroke-width="2" marker-end="url(#arrow)" />
                <text x="340" y="98" text-anchor="middle" fill="#16a34a" font-family="sans-serif" font-size="10" font-weight="bold">SQL / ORM</text>

                <!-- Control Plane -> Compute (Job Queue / Invocations) -->
                <path d="M 310 160 L 670 160" stroke="#7c3aed" stroke-width="2" stroke-dasharray="4,4" marker-end="url(#arrow-purple)" />
                <text x="490" y="152" text-anchor="middle" fill="#7c3aed" font-family="sans-serif" font-size="10" font-weight="bold">Async Job Dispatch &amp; Heartbeat</text>

                <!-- 110 -> Storage -->
                <line x1="170" y1="230" x2="250" y2="330" stroke="#d97706" stroke-width="1.5" marker-end="url(#arrow)" />

                <!-- 94 -> Storage -->
                <line x1="795" y1="230" x2="700" y2="330" stroke="#d97706" stroke-width="1.5" marker-end="url(#arrow)" />
            </svg>
        </div>
    </div>
</div>

<!-- Detailed Component Breakdown -->
<div class="row g-4">
    <div class="col-md-4">
        <div class="card h-100 border-0 shadow-sm border-top border-4 border-primary">
            <div class="card-body">
                <h5 class="fw-bold text-dark mb-2">1. Control Plane</h5>
                <p class="text-muted small">
                    Coordinates state transitions, research governance, scientific reasoning context, and user interfaces.
                </p>
                <ul class="small text-secondary ps-3 mb-0">
                    <li><strong>Web UI:</strong> Apache / PHP 8.3 research workspace with Bootstrap 5.</li>
                    <li><strong>Backend Engine:</strong> FastAPI (Python 3.12, Uvicorn) managing all business logic and relational state.</li>
                    <li><strong>Context Assembly:</strong> <code>ScientificContextService</code> assembles multi-component prompts.</li>
                    <li><strong>Gateway:</strong> LLM Gateway with schema validation, retry budgets, and JSON repair.</li>
                </ul>
            </div>
        </div>
    </div>

    <div class="col-md-4">
        <div class="card h-100 border-0 shadow-sm border-top border-4 border-success">
            <div class="card-body">
                <h5 class="fw-bold text-dark mb-2">2. Empirical Ground Truth &amp; Data Store</h5>
                <p class="text-muted small">
                    Empirical data layer providing immutable biodiversity records and the relational world model.
                </p>
                <ul class="small text-secondary ps-3 mb-0">
                    <li><strong>GBIF/OBIS Cache:</strong> Millions of georeferenced specimen occurrence records and imagery.</li>
                    <li><strong>World Model:</strong> 16 relational entities tracking projects, plans, DAG steps, capabilities, and runs.</li>
                    <li><strong>Taxonomic Validation:</strong> WoRMS (World Register of Marine Species) AphiaID lookup.</li>
                    <li><strong>Migrations:</strong> Managed exclusively via Alembic version scripts.</li>
                </ul>
            </div>
        </div>
    </div>

    <div class="col-md-4">
        <div class="card h-100 border-0 shadow-sm border-top border-4 border-purple" style="border-top-color: #7c3aed !important;">
            <div class="card-body">
                <h5 class="fw-bold text-dark mb-2">3. GPU Compute Worker</h5>
                <p class="text-muted small">
                    High-performance hardware node for model training, inference, and batch representation extraction.
                </p>
                <ul class="small text-secondary ps-3 mb-0">
                    <li><strong>Vision Models:</strong> DINOv3 self-supervised representation extractor (384-dimensional embeddings).</li>
                    <li><strong>Classifiers:</strong> ResNet-50 supervised taxonomic classifiers.</li>
                    <li><strong>Reproducibility:</strong> Parameterized execution via Papermill and isolated conda/venv environments.</li>
                    <li><strong>Artifact Outputs:</strong> Writes model weights, matrices, and plot figures directly to project storage.</li>
                </ul>
            </div>
        </div>
    </div>
</div>

<?php require_once __DIR__ . '/includes/help_footer.php'; ?>
