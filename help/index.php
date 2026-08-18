<?php

declare(strict_types=1);

$activeTopic = 'index';
$pageTitle = 'Help & Documentation Portal — Biodiversity AI Scientist';

require_once __DIR__ . '/includes/help_header.php';

?>

<div class="help-hero text-center mb-4">
    <span class="badge bg-primary-subtle text-primary border border-primary-subtle text-uppercase tracking-wide px-3 py-1 mb-2">Knowledge Base &amp; Technical Manual</span>
    <h1 class="display-5 fw-bold mb-2">Biodiversity AI Scientist Help Documentation</h1>
    <p class="lead text-light-50 mb-4 max-w-2xl mx-auto" style="max-width: 800px;">
        Comprehensive architecture guides, researcher workflows, and technical references for the agentic scientific discovery platform.
    </p>

    <div class="row justify-content-center">
        <div class="col-md-6">
            <div class="input-group input-group-lg shadow-sm">
                <span class="input-group-text bg-white border-end-0 text-muted"><i class="bi bi-search"></i></span>
                <input type="text" id="helpSearchInput" class="form-control border-start-0" placeholder="Search topics, phases, architectures, or schemas..." onkeyup="filterHelpTopics()">
            </div>
        </div>
    </div>
</div>

<!-- Section 1: Foundations & Architecture -->
<div class="mb-5 topic-section">
    <div class="d-flex align-items-center gap-2 mb-3">
        <span class="badge bg-primary text-white"><i class="bi bi-diagram-3 me-1"></i>01</span>
        <h2 class="h4 mb-0 fw-bold">Platform Foundations &amp; System Overview</h2>
    </div>
    <div class="row g-4">
        <div class="col-md-6 col-lg-4 help-item" data-keywords="architecture server 110 server 94 mysql 112 gpu cuda fast api sqlalchemy alembic svg data flow">
            <div class="card help-card p-4 shadow-sm" onclick="location.href='architecture.php<?= $projParam ?>'">
                <div class="help-icon-circle bg-primary-subtle text-primary">
                    <i class="bi bi-diagram-3-fill"></i>
                </div>
                <h3 class="h5 fw-bold text-dark mb-2">System Architecture &amp; Data Flow</h3>
                <p class="text-muted small mb-0">
                    Tri-node physical infrastructure (Server 110 Control Plane, Server 94 GPU Compute, MySQL 112 DWH Occurrence Layer), REST APIs, and artifact storage trees.
                </p>
            </div>
        </div>

        <div class="col-md-6 col-lg-4 help-item" data-keywords="user manual workflow walkthrough lifecycle project dataset question hypothesis plan dag analysis">
            <div class="card help-card p-4 shadow-sm" onclick="location.href='user_manual.php<?= $projParam ?>'">
                <div class="help-icon-circle bg-indigo-subtle text-indigo" style="background-color: #ede9fe; color: #6d28d9;">
                    <i class="bi bi-book-fill"></i>
                </div>
                <h3 class="h5 fw-bold text-dark mb-2">End-to-End Researcher Manual</h3>
                <p class="text-muted small mb-0">
                    Step-by-step researcher workflow from project initialization through DWH occurrences, hypothesis generation, research plan review, DAG sequencing, and experiment runs.
                </p>
            </div>
        </div>

        <div class="col-md-6 col-lg-4 help-item" data-keywords="faq troubleshooting questions errors retries rate limits fallback gpu memory alembic restart">
            <div class="card help-card p-4 shadow-sm" onclick="location.href='faq.php<?= $projParam ?>'">
                <div class="help-icon-circle bg-warning-subtle text-warning">
                    <i class="bi bi-question-circle-fill"></i>
                </div>
                <h3 class="h5 fw-bold text-dark mb-2">FAQ &amp; Operational Troubleshooting</h3>
                <p class="text-muted small mb-0">
                    Frequently asked questions, LLM gateway fallback behaviors, GPU memory constraints, service daemon lifecycles, and database migrations.
                </p>
            </div>
        </div>
    </div>
</div>

<!-- Section 2: Discovery & Scientific Reasoning -->
<div class="mb-5 topic-section">
    <div class="d-flex align-items-center gap-2 mb-3">
        <span class="badge bg-warning text-dark"><i class="bi bi-lightbulb me-1"></i>02</span>
        <h2 class="h4 mb-0 fw-bold">Scientific Discovery &amp; Hypothesis Generation</h2>
    </div>
    <div class="row g-4">
        <div class="col-md-6 col-lg-4 help-item" data-keywords="brainstorming ideation session candidates cumulative multi-turn prompt ground truth gbif dwh occurrences">
            <div class="card help-card p-4 shadow-sm" onclick="location.href='brainstorming.php<?= $projParam ?>'">
                <div class="help-icon-circle bg-warning-subtle text-warning-emphasis">
                    <i class="bi bi-lightbulb-fill"></i>
                </div>
                <h3 class="h5 fw-bold text-dark mb-2">Brainstorming &amp; Ideation</h3>
                <p class="text-muted small mb-0">
                    Cumulative multi-turn AI dialogues grounded with DWH occurrence intelligence, and automated candidate question/hypothesis promotion.
                </p>
            </div>
        </div>

        <div class="col-md-6 col-lg-4 help-item" data-keywords="phase 6 research plan analytical stages evidence required validation criteria review approval versioning">
            <div class="card help-card p-4 shadow-sm" onclick="location.href='research_plans.php<?= $projParam ?>'">
                <div class="help-icon-circle bg-info-subtle text-info-emphasis">
                    <i class="bi bi-file-earmark-text-fill"></i>
                </div>
                <h3 class="h5 fw-bold text-dark mb-2">Phase 6: Research Plans</h3>
                <p class="text-muted small mb-0">
                    Structured research plan formulation, 7-section scientific schemas, version control, analytical stages, and researcher approval lifecycles.
                </p>
            </div>
        </div>

        <div class="col-md-6 col-lg-4 help-item" data-keywords="phase 7 context engine provenance fact research plan gbif token budget unified context assembly">
            <div class="card help-card p-4 shadow-sm" onclick="location.href='scientific_context.php<?= $projParam ?>'">
                <div class="help-icon-circle bg-success-subtle text-success">
                    <i class="bi bi-intersect"></i>
                </div>
                <h3 class="h5 fw-bold text-dark mb-2">Phase 7: Scientific Context Engine</h3>
                <p class="text-muted small mb-0">
                    Unified context assembly, strict provenance tagging ([FACT], [RESEARCH_PLAN], [GBIF_DWH_OCCURRENCE]), and token budget constraints.
                </p>
            </div>
        </div>
    </div>
</div>

<!-- Section 3: Sequencing & Execution -->
<div class="mb-5 topic-section">
    <div class="d-flex align-items-center gap-2 mb-3">
        <span class="badge bg-success text-white"><i class="bi bi-diagram-2 me-1"></i>03</span>
        <h2 class="h4 mb-0 fw-bold">Step Sequencing, Capabilities &amp; Execution</h2>
    </div>
    <div class="row g-4">
        <div class="col-md-6 col-lg-4 help-item" data-keywords="phase 8 investigation plan dag step dependency kahn topological sort readiness cycle prevention">
            <div class="card help-card p-4 shadow-sm" onclick="location.href='investigation_planning.php<?= $projParam ?>'">
                <div class="help-icon-circle bg-primary-subtle text-primary">
                    <i class="bi bi-diagram-2-fill"></i>
                </div>
                <h3 class="h5 fw-bold text-dark mb-2">Phase 8: Investigation Planning (DAG)</h3>
                <p class="text-muted small mb-0">
                    Decomposition of research questions into non-prescriptive Directed Acyclic Graphs, relational dependency edges, Kahn topological sorting, and readiness states.
                </p>
            </div>
        </div>

        <div class="col-md-6 col-lg-4 help-item" data-keywords="phase 9 phase b01 scientific capability two-tier physical implementation scope dinov3 resnet worms gap 14 domains semantic contracts">
            <div class="card help-card p-4 shadow-sm" onclick="location.href='capabilities.php<?= $projParam ?>'">
                <div class="help-icon-circle bg-secondary-subtle text-secondary">
                    <i class="bi bi-tools"></i>
                </div>
                <h3 class="h5 fw-bold text-dark mb-2">Phase 9 &amp; B01: Capability Taxonomy &amp; Two-Tier Registry</h3>
                <p class="text-muted small mb-0">
                    Two-tier physical decoupling, 14 standardized biodiversity domains, implementation-level 4-tier scope governance, 14 canonical semantic data contracts, and usable execution path gap detection.
                </p>
            </div>
        </div>

        <div class="col-md-6 col-lg-4 help-item" data-keywords="phase 10 analyses experiment runs parameter pre specification metrics artifacts results storage">
            <div class="card help-card p-4 shadow-sm" onclick="location.href='analyses.php<?= $projParam ?>'">
                <div class="help-icon-circle bg-danger-subtle text-danger">
                    <i class="bi bi-flask-fill"></i>
                </div>
                <h3 class="h5 fw-bold text-dark mb-2">Phase 10: Empirical Analyses &amp; Runs</h3>
                <p class="text-muted small mb-0">
                    Pre-specifying analysis plans, execution runs, metric logging (F1, accuracy, silhouette score), and project artifact persistence.
                </p>
            </div>
        </div>
    </div>
</div>

<!-- Section 4: Engineering & Technical Reference -->
<div class="mb-4 topic-section">
    <div class="d-flex align-items-center gap-2 mb-3">
        <span class="badge bg-dark text-white"><i class="bi bi-code-square me-1"></i>04</span>
        <h2 class="h4 mb-0 fw-bold">Engineering Specifications &amp; Schemas</h2>
    </div>
    <div class="row g-4">
        <div class="col-12 help-item" data-keywords="technical reference database schema mysql tables foreign keys rest api fastapi openapi llm contracts repair json">
            <div class="card help-card p-4 shadow-sm" onclick="location.href='technical_reference.php<?= $projParam ?>'">
                <div class="row align-items-center">
                    <div class="col-auto">
                        <div class="help-icon-circle bg-dark text-white mb-0">
                            <i class="bi bi-code-square"></i>
                        </div>
                    </div>
                    <div class="col">
                        <h3 class="h5 fw-bold text-dark mb-1">Database Schema, REST API &amp; Technical Reference</h3>
                        <p class="text-muted small mb-0">
                            Complete MySQL schema reference (all 16 relational entities, primary/foreign keys, indexes), FastAPI OpenAPI endpoints, LLM gateway templates, and JSON repair engine.
                        </p>
                    </div>
                    <div class="col-auto">
                        <span class="btn btn-sm btn-outline-primary">View Full Specs ↗</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
function filterHelpTopics() {
    const input = document.getElementById('helpSearchInput').value.toLowerCase();
    const items = document.querySelectorAll('.help-item');
    const sections = document.querySelectorAll('.topic-section');

    items.forEach(item => {
        const text = item.innerText.toLowerCase();
        const keywords = item.getAttribute('data-keywords') || '';
        if (text.includes(input) || keywords.includes(input)) {
            item.style.display = '';
        } else {
            item.style.display = 'none';
        }
    });

    sections.forEach(section => {
        const visibleItems = section.querySelectorAll('.help-item:not([style*="display: none"])');
        section.style.display = visibleItems.length > 0 ? '' : 'none';
    });
}
</script>

<?php require_once __DIR__ . '/includes/help_footer.php'; ?>
