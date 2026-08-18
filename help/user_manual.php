<?php

declare(strict_types=1);

$activeTopic = 'user_manual';
$pageTitle = 'End-to-End Researcher User Manual — AI Scientist Help';

require_once __DIR__ . '/includes/help_header.php';

?>

<div class="row mb-4">
    <div class="col-12">
        <div class="d-flex align-items-center gap-2 mb-1">
            <span class="badge bg-indigo text-white text-uppercase tracking-wide" style="background-color: #6d28d9;">Workflow Guide</span>
            <h1 class="h3 mb-0 fw-bold">End-to-End Researcher User Manual</h1>
        </div>
        <p class="text-muted mb-0">
            A comprehensive, phase-by-phase operational walkthrough for conducting reproducible scientific investigations on the platform.
        </p>
    </div>
</div>

<!-- Workflow Steps Timeline -->
<div class="card shadow-sm border-0 mb-5">
    <div class="card-body p-4">
        <div class="row g-4">
            
            <!-- Phase 1 & 2 -->
            <div class="col-md-6">
                <div class="p-3 bg-light rounded border h-100">
                    <div class="d-flex align-items-center gap-2 mb-2">
                        <span class="badge bg-primary text-white">Phase 1 &amp; 2</span>
                        <h5 class="fw-bold text-dark mb-0">Project &amp; Focal Research Questions</h5>
                    </div>
                    <p class="text-secondary small mb-2">
                        Create a project workspace with an overarching biological objective. Formulate one or more canonical <strong>ResearchQuestions</strong> to guide the study.
                    </p>
                    <ul class="small text-muted ps-3 mb-0">
                        <li>Navigate to <code>Projects &gt; New Project</code>.</li>
                        <li>Enter title, scientific domain (e.g., <em>Gastropoda: Nassariidae</em>), and core objective.</li>
                        <li>Define primary focal questions with assigned priorities.</li>
                    </ul>
                </div>
            </div>

            <!-- Phase 3 & 4 -->
            <div class="col-md-6">
                <div class="p-3 bg-light rounded border h-100">
                    <div class="d-flex align-items-center gap-2 mb-2">
                        <span class="badge bg-warning text-dark">Phase 3 &amp; 4</span>
                        <h5 class="fw-bold text-dark mb-0">Brainstorming &amp; Hypothesis Promotion</h5>
                    </div>
                    <p class="text-secondary small mb-2">
                        Engage in cumulative multi-turn scientific dialogues with the AI, grounded in real GBIF/OBIS DWH occurrence data and specimen metadata.
                    </p>
                    <ul class="small text-muted ps-3 mb-0">
                        <li>Open the <strong>Brainstorming</strong> tab.</li>
                        <li>Discuss morphological traits, cryptic variation, or ecological distributions.</li>
                        <li>Review candidate questions/hypotheses proposed by the AI and click <strong>Accept &amp; Promote</strong> to save them directly to the database.</li>
                    </ul>
                </div>
            </div>

            <!-- Phase 5 & 6 -->
            <div class="col-md-6">
                <div class="p-3 bg-light rounded border h-100">
                    <div class="d-flex align-items-center gap-2 mb-2">
                        <span class="badge bg-info text-dark">Phase 5 &amp; 6</span>
                        <h5 class="fw-bold text-dark mb-0">Research Plans &amp; Approval Governance</h5>
                    </div>
                    <p class="text-secondary small mb-2">
                        Generate structured <strong>ResearchPlans</strong> with defined objectives, background, analytical stages, evidence requirements, and validation strategies.
                    </p>
                    <ul class="small text-muted ps-3 mb-0">
                        <li>Navigate to <code>Research Plans</code>.</li>
                        <li>Click <strong>Generate Plan with AI</strong> or author manually.</li>
                        <li>Review the 7-section plan and promote its status from <code>draft</code> to <code>approved</code>.</li>
                    </ul>
                </div>
            </div>

            <!-- Phase 7 & 8 -->
            <div class="col-md-6">
                <div class="p-3 bg-light rounded border h-100">
                    <div class="d-flex align-items-center gap-2 mb-2">
                        <span class="badge bg-success text-white">Phase 7 &amp; 8</span>
                        <h5 class="fw-bold text-dark mb-0">Investigation DAG &amp; Step Sequencing</h5>
                    </div>
                    <p class="text-secondary small mb-2">
                        Decompose an approved research plan into an explicit Directed Acyclic Graph (DAG) of operational <strong>InvestigationSteps</strong> with prerequisite dependencies.
                    </p>
                    <ul class="small text-muted ps-3 mb-0">
                        <li>Open <code>Investigation Plan</code>.</li>
                        <li>Click <strong>Generate Investigation DAG with AI</strong>.</li>
                        <li>Inspect the topologically sorted execution stages and dependency badges.</li>
                    </ul>
                </div>
            </div>

            <!-- Phase 9 -->
            <div class="col-md-6">
                <div class="p-3 bg-light rounded border h-100">
                    <div class="d-flex align-items-center gap-2 mb-2">
                        <span class="badge bg-secondary text-white">Phase 9</span>
                        <h5 class="fw-bold text-dark mb-0">Capability Matching &amp; Tool Selection</h5>
                    </div>
                    <p class="text-secondary small mb-2">
                        Match each investigation step to registered tools (e.g. DINOv3 embedding extractor, WoRMS taxa resolver, ResNet classifier) or identify Capability Gaps.
                    </p>
                    <ul class="small text-muted ps-3 mb-0">
                        <li>Click <strong>Match Capabilities with AI</strong> in the toolbar.</li>
                        <li>Review automated selections, scientific rationales, and rejected alternatives.</li>
                        <li>Override tool selection or track unresolved <strong>Capability Gaps</strong> in the registry.</li>
                    </ul>
                </div>
            </div>

            <!-- Phase 10 -->
            <div class="col-md-6">
                <div class="p-3 bg-light rounded border h-100">
                    <div class="d-flex align-items-center gap-2 mb-2">
                        <span class="badge bg-danger text-white">Phase 10</span>
                        <h5 class="fw-bold text-dark mb-0">Empirical Analyses &amp; Execution</h5>
                    </div>
                    <p class="text-secondary small mb-2">
                        Pre-specify computational parameters, trigger experiment runs, and capture metrics, confusion matrices, and model weight artifacts.
                    </p>
                    <ul class="small text-muted ps-3 mb-0">
                        <li>Navigate to <code>Experiments (Analyses)</code>.</li>
                        <li>Create an <strong>AnalysisPlan</strong> bound to an investigation step.</li>
                        <li>Trigger execution runs and inspect performance metrics and generated artifact files.</li>
                    </ul>
                </div>
            </div>

        </div>
    </div>
</div>

<?php require_once __DIR__ . '/includes/help_footer.php'; ?>
