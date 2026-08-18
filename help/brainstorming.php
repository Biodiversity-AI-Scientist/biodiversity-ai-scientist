<?php

declare(strict_types=1);

$activeTopic = 'brainstorming';
$pageTitle = 'Brainstorming & Hypothesis Ideation — AI Scientist Help';

require_once __DIR__ . '/includes/help_header.php';

?>

<div class="row mb-4">
    <div class="col-12">
        <div class="d-flex align-items-center gap-2 mb-1">
            <span class="badge bg-warning text-dark text-uppercase tracking-wide">Scientific Discovery</span>
            <h1 class="h3 mb-0 fw-bold">Brainstorming &amp; Hypothesis Ideation</h1>
        </div>
        <p class="text-muted mb-0">
            Cumulative multi-turn AI reasoning, grounded DWH occurrence intelligence, and automated candidate entity promotion.
        </p>
    </div>
</div>

<div class="row g-4">
    <div class="col-lg-8">
        <div class="card shadow-sm border-0 mb-4">
            <div class="card-header bg-white py-3">
                <h5 class="fw-bold text-dark mb-0"><i class="bi bi-chat-dots text-primary me-2"></i>Cumulative Dialogue Architecture</h5>
            </div>
            <div class="card-body p-4">
                <p>
                    Unlike stateless chatbots, the <strong>Brainstorming Session</strong> maintains an explicit persistent sequence of conversation turns stored in the <code>brainstorming_turns</code> database table.
                </p>

                <h6 class="fw-bold text-dark mt-4 mb-2">Key Operating Principles:</h6>
                <ol class="ps-3 text-secondary small">
                    <li class="mb-2"><strong>Ground Truth Occurrence Grounding:</strong> At the start of a session, the backend queries the empirical data store for real occurrence counts, geographic bounding boxes, and image availability for the target taxa.</li>
                    <li class="mb-2"><strong>Cumulative Context:</strong> The LLM Gateway passes the last <code>N</code> conversation turns to ensure continuity across follow-up questions and refined hypotheses.</li>
                    <li class="mb-2"><strong>Structured Candidates:</strong> Every assistant reply extracts concrete candidate <strong>Questions</strong> and <strong>Hypotheses</strong> into the <code>session_candidates</code> table with status <code>proposed</code>.</li>
                </ol>

                <div class="p-3 bg-light rounded border mt-4">
                    <h6 class="fw-bold text-dark mb-2"><i class="bi bi-arrow-up-right-circle text-success me-2"></i>Promoting Candidates to the Scientific World Model</h6>
                    <p class="small text-muted mb-0">
                        When a researcher clicks <strong>Accept &amp; Promote</strong> on a candidate card, the system creates a first-class <code>ResearchQuestion</code> or <code>Hypothesis</code> row in the database, permanently linked to the project and available for Research Plans and Investigation DAG sequencing.
                    </p>
                </div>
            </div>
        </div>
    </div>

    <div class="col-lg-4">
        <div class="card shadow-sm border-0 mb-4">
            <div class="card-header bg-white py-3">
                <h6 class="fw-bold text-dark mb-0"><i class="bi bi-sliders me-2"></i>Session State &amp; Controls</h6>
            </div>
            <div class="card-body p-3">
                <div class="mb-3">
                    <span class="badge bg-light text-dark border w-100 p-2 text-start mb-2">
                        <i class="bi bi-database me-1 text-primary"></i> Table: <code>brainstorming_turns</code>
                    </span>
                    <span class="badge bg-light text-dark border w-100 p-2 text-start mb-2">
                        <i class="bi bi-list-check me-1 text-success"></i> Table: <code>session_candidates</code>
                    </span>
                </div>
                <div class="small text-muted">
                    <strong>Candidate Statuses:</strong>
                    <ul class="ps-3 mt-1 mb-0">
                        <li><code>proposed</code>: Newly suggested by AI.</li>
                        <li><code>accepted</code>: Promoted to database.</li>
                        <li><code>edited_and_accepted</code>: Modified by researcher and saved.</li>
                        <li><code>rejected</code>: Dismissed by researcher.</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
</div>

<?php require_once __DIR__ . '/includes/help_footer.php'; ?>
