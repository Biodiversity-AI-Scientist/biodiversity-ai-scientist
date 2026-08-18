<?php

require_once __DIR__ . '/includes/api.php';

header('Content-Type: application/json');

try {

    $projects = api_get('/projects');

    echo json_encode(
        $projects,
        JSON_PRETTY_PRINT
    );

} catch (Throwable $e) {

    http_response_code(500);

    echo json_encode([
        'error' => $e->getMessage()
    ]);
}
