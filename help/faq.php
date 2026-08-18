<?php

declare(strict_types=1);

$activeTopic = 'faq';
$pageTitle = 'FAQ & Operational Troubleshooting — AI Scientist Help';

require_once __DIR__ . '/includes/help_header.php';

?>

<div class="row mb-4">
    <div class="col-12">
        <div class="d-flex align-items-center gap-2 mb-1">
            <span class="badge bg-secondary text-white text-uppercase tracking-wide">Operations</span>
            <h1 class="h3 mb-0 fw-bold">Frequently Asked Questions &amp; Troubleshooting</h1>
        </div>
        <p class="text-muted mb-0">
            Operational guidelines, common error resolutions, LLM retry behaviors, and database administration tips.
        </p>
    </div>
</div>

<div class="row g-4">
    <div class="col-lg-12">
        <div class="accordion shadow-sm" id="faqAccordion">

            <!-- FAQ 1 -->
            <div class="accordion-item">
                <h2 class="accordion-header">
                    <button class="accordion-button fw-bold text-dark" type="button" data-bs-toggle="collapse" data-bs-target="#faq1">
                        <i class="bi bi-question-circle text-primary me-2"></i> How does the system prevent hallucinated or ungrounded data generation?
                    </button>
                </h2>
                <div id="faq1" class="accordion-collapse collapse show" data-bs-parent="#faqAccordion">
                    <div class="accordion-body text-secondary small">
                        The platform enforces Phase 7 <strong>Scientific Context Engine</strong> provenance rules. Before prompt rendering, empirical facts from MySQL 112 (occurrences, taxonomic records) and relational models (approved research plans, hypotheses) are explicitly labeled with <code>[FACT]</code>, <code>[GBIF_DWH_OCCURRENCE]</code>, and <code>[RESEARCH_PLAN]</code> tags. The LLM Gateway strictly separates empirical facts from model interpretations.
                    </div>
                </div>
            </div>

            <!-- FAQ 2 -->
            <div class="accordion-item">
                <h2 class="accordion-header">
                    <button class="accordion-button collapsed fw-bold text-dark" type="button" data-bs-toggle="collapse" data-bs-target="#faq2">
                        <i class="bi bi-cpu text-primary me-2"></i> What happens if an LLM API provider fails, rate-limits, or times out?
                    </button>
                </h2>
                <div id="faq2" class="accordion-collapse collapse" data-bs-parent="#faqAccordion">
                    <div class="accordion-body text-secondary small">
                        The <code>LLMGateway</code> executes an exponential backoff retry loop up to <code>LLM_MAX_ATTEMPTS</code>. If structured output validation fails due to minor JSON syntax errors, the <code>repair_and_parse_json()</code> repair engine repairs truncated or malformed responses. In Phase 9 capability selection, if the LLM remains unreachable, the system automatically falls back to deterministic candidate matching without breaking the workflow.
                    </div>
                </div>
            </div>

            <!-- FAQ 3 -->
            <div class="accordion-item">
                <h2 class="accordion-header">
                    <button class="accordion-button collapsed fw-bold text-dark" type="button" data-bs-toggle="collapse" data-bs-target="#faq3">
                        <i class="bi bi-database-gear text-primary me-2"></i> How are database schema changes managed?
                    </button>
                </h2>
                <div id="faq3" class="accordion-collapse collapse" data-bs-parent="#faqAccordion">
                    <div class="accordion-body text-secondary small">
                        Database evolution is managed exclusively via Alembic migration scripts in <code>migrations/versions/</code>. Manual <code>ALTER TABLE</code> statements on production schemas are strictly prohibited to maintain migration history integrity and MySQL 5.7/8.0 compatibility.
                    </div>
                </div>
            </div>

            <!-- FAQ 4 -->
            <div class="accordion-item">
                <h2 class="accordion-header">
                    <button class="accordion-button collapsed fw-bold text-dark" type="button" data-bs-toggle="collapse" data-bs-target="#faq4">
                        <i class="bi bi-diagram-2 text-primary me-2"></i> Why is an Investigation Step marked "Blocked"?
                    </button>
                </h2>
                <div id="faq4" class="accordion-collapse collapse" data-bs-parent="#faqAccordion">
                    <div class="accordion-body text-secondary small">
                        A step's readiness is evaluated across multiple factors:
                        <ul class="mt-2 mb-0 ps-3">
                            <li><strong>Prerequisite Blocked:</strong> One or more upstream prerequisite steps in the DAG have not reached <code>completed</code> status.</li>
                            <li><strong>Capability Blocked:</strong> The step requires a computational capability, but no matching tool is registered in the registry or an unresolved <code>CapabilityGap</code> exists.</li>
                        </ul>
                    </div>
                </div>
            </div>

            <!-- FAQ 5 -->
            <div class="accordion-item">
                <h2 class="accordion-header">
                    <button class="accordion-button collapsed fw-bold text-dark" type="button" data-bs-toggle="collapse" data-bs-target="#faq5">
                        <i class="bi bi-tools text-primary me-2"></i> How do I resolve a Capability Gap?
                    </button>
                </h2>
                <div id="faq5" class="accordion-collapse collapse" data-bs-parent="#faqAccordion">
                    <div class="accordion-body text-secondary small">
                        Navigate to <code>Capabilities &gt; Capability Gaps</code>. You can register a new software adapter in the application inventory, assign an alternative tool via the <strong>Researcher Override</strong> modal, or update the gap's status to <code>in_development</code> or <code>resolved</code>.
                    </div>
                </div>
            </div>

        </div>
    </div>
</div>

<?php require_once __DIR__ . '/includes/help_footer.php'; ?>
