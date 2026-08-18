<?php

declare(strict_types=1);

$topicKeys = array_keys($topics);
$currentIndex = array_search($activeTopic, $topicKeys, true);

$prevTopic = ($currentIndex !== false && $currentIndex > 0) ? $topics[$topicKeys[$currentIndex - 1]] : null;
$nextTopic = ($currentIndex !== false && $currentIndex < count($topicKeys) - 1) ? $topics[$topicKeys[$currentIndex + 1]] : null;

?>

    <!-- Next / Previous Pager (when on a topic page) -->
    <?php if ($activeTopic !== 'index' && ($prevTopic || $nextTopic)): ?>
        <div class="row g-3 mt-5 pt-4 border-top">
            <div class="col-6 text-start">
                <?php if ($prevTopic): ?>
                    <a href="<?= $prevTopic['file'] ?><?= $projParam ?>" class="btn btn-outline-secondary btn-sm px-3">
                        <i class="bi bi-arrow-left me-1"></i> Previous: <?= htmlspecialchars($prevTopic['title'], ENT_QUOTES, 'UTF-8') ?>
                    </a>
                <?php endif; ?>
            </div>
            <div class="col-6 text-end">
                <?php if ($nextTopic): ?>
                    <a href="<?= $nextTopic['file'] ?><?= $projParam ?>" class="btn btn-primary btn-sm px-3">
                        Next: <?= htmlspecialchars($nextTopic['title'], ENT_QUOTES, 'UTF-8') ?> <i class="bi bi-arrow-right ms-1"></i>
                    </a>
                <?php endif; ?>
            </div>
        </div>
    <?php endif; ?>

    <footer class="mt-5 pt-4 border-top text-center text-muted small pb-4">
        <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
            <div>
                © 2026 Biodiversity AI Scientist Documentation System • Grounded Scientific World Model
            </div>
            <div>
                <a href="index.php<?= $projParam ?>" class="text-decoration-none text-muted me-3">Help Index</a>
                <a href="architecture.php<?= $projParam ?>" class="text-decoration-none text-muted me-3">Architecture</a>
                <a href="technical_reference.php<?= $projParam ?>" class="text-decoration-none text-muted">Technical Specs</a>
            </div>
        </div>
    </footer>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
