<?php

declare(strict_types=1);

$query = $_SERVER['QUERY_STRING'] ?? '';
$target = 'help/brainstorming.php' . ($query !== '' ? '?' . $query : '');

header('Location: ' . $target, true, 302);
exit;
