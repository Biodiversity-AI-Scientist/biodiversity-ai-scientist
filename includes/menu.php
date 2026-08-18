<?php

/*
 * Expected variables:
 *
 * $projectId   int
 * $activePage  string
 */

$menuItems = [
    'overview' => [
        'label' => 'Overview',
        'url' => 'project.php?project_id=' . $projectId,
        'enabled' => true,
    ],

    'brainstorming' => [
        'label' => 'Brainstorming',
        'url'   => 'brainstorming.php?project_id=' . $projectId,
        'enabled' => true,
    ],

    'research_plans' => [
        'label' => 'Research Plans',
        'url'   => 'research_plans.php?project_id=' . $projectId,
        'enabled' => true,
    ],

    'investigation_plan' => [
        'label' => 'Investigation Plan',
        'url'   => 'investigation_plan.php?project_id=' . $projectId,
        'enabled' => true,
    ],

    'questions' => [
        'label' => 'Questions',
        'url'   => 'questions.php?project_id=' . $projectId,
        'enabled' => true,
    ],


    'hypotheses' => [
        'label' => 'Hypotheses',
        'url'   => 'hypotheses.php?project_id=' . $projectId,
        'enabled' => true,
    ],

    'dataset' => [
    	'label' => 'Dataset',
	'url'   => 'dataset.php?project_id=' . $projectId,
    	'enabled' => true,
    ],

    'analyses' => [
        'label' => 'Experiments',
        'url'   => 'analyses.php?project_id=' . $projectId,
        'enabled' => true,
    ],

    'capabilities' => [
        'label' => 'Capabilities',
        'url'   => 'capabilities.php?project_id=' . $projectId,
        'enabled' => true,
    ],


    'evidence' => [
        'label' => 'Evidence',
        'url'   => 'evidence.php?project_id=' . $projectId,
        'enabled' => false,
    ],

    'literature' => [
        'label' => 'Literature',
        'url'   => 'literature.php?project_id=' . $projectId,
        'enabled' => false,
    ],

    'review' => [
        'label' => 'Review',
        'url'   => 'review.php?project_id=' . $projectId,
        'enabled' => false,
    ],

    'notebook' => [
        'label' => 'Notebook',
        'url'   => 'notebook.php?project_id=' . $projectId,
        'enabled' => false,
    ],

    'artifacts' => [
        'label' => 'Artifacts',
        'url'   => 'artifacts.php?project_id=' . $projectId,
        'enabled' => false,
    ],
];

?>

<aside
    class="col-md-3 col-lg-2
           bg-white
           border-end
           min-vh-100
           p-3">

    <div class="small text-uppercase
                text-muted
                fw-semibold
                mb-2">

        Research workspace

    </div>

    <nav>

        <?php foreach ($menuItems as $key => $item): ?>

            <?php

            $classes = ['sidebar-link'];

            if ($key === $activePage) {
                $classes[] = 'active';
            }

            if (!$item['enabled']) {
                $classes[] = 'disabled';
            }

            ?>

            <a
                class="<?= implode(' ', $classes) ?>"
                href="<?= $item['enabled']
                    ? htmlspecialchars($item['url'], ENT_QUOTES, 'UTF-8')
                    : '#' ?>">

                <?= htmlspecialchars(
                    $item['label'],
                    ENT_QUOTES,
                    'UTF-8'
                ) ?>

            </a>

        <?php endforeach; ?>

    </nav>

    <div class="small text-uppercase text-muted fw-semibold mt-4 mb-2">Documentation</div>
    <nav>
        <a class="sidebar-link" href="/ai-scientist/help/index.php<?= !empty($projectId) ? '?project_id=' . (int)$projectId : '' ?>">
            <i class="bi bi-book me-1 text-primary"></i> Help Center
        </a>
    </nav>

</aside>
