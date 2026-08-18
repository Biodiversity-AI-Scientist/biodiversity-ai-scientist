<?php

$url = 'http://127.0.0.1/ai-scientist/api/health/database';

$ch = curl_init($url);

curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_CONNECTTIMEOUT => 3,
    CURLOPT_TIMEOUT => 10,
    CURLOPT_HTTPHEADER => [
        'Accept: application/json'
    ],
]);

$response = curl_exec($ch);

if ($response === false) {
    http_response_code(500);
    die('API error: ' . htmlspecialchars(curl_error($ch)));
}

$status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

header('Content-Type: application/json');
http_response_code($status);

echo $response;

