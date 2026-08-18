<?php

declare(strict_types=1);

require_once __DIR__ . '/includes/api.php';

header('Content-Type: application/json; charset=utf-8');

$action = $_GET['action'] ?? '';
$rawBody = file_get_contents('php://input');
$body = json_decode($rawBody, true) ?? [];

try {
    if ($action === 'inspect_packet') {
        $result = api_post('/orchestrator/inspect-packet', $body);
        echo json_encode($result);
        exit;
    }

    if ($action === 'compare_taxa') {
        $result = api_post('/taxa/compare-priorities', $body);
        echo json_encode($result);
        exit;
    }

    if ($action === 'route_decision') {
        $result = api_post('/orchestrator/route-decision', $body);
        echo json_encode($result);
        exit;
    }

    http_response_code(400);
    echo json_encode(['error' => 'Invalid action: ' . htmlspecialchars($action)]);
} catch (Throwable $e) {
    http_response_code(500);
    echo json_encode(['error' => $e->getMessage()]);
}
