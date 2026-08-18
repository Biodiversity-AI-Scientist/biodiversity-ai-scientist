<?php

declare(strict_types=1);

function get_bais_api_base_url(): string {
    $envUrl = getenv('BAIS_API_URL');
    if (!empty($envUrl)) {
        return rtrim($envUrl, '/');
    }
    // Check if local .env defines custom port
    $envFile = dirname(__DIR__) . '/.env';
    if (file_exists($envFile)) {
        $lines = @file($envFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) ?: [];
        $port = null;
        $host = '127.0.0.1';
        foreach ($lines as $line) {
            $line = trim($line);
            if (str_starts_with($line, 'APP_PORT=')) {
                $port = trim(substr($line, 9));
            } elseif (str_starts_with($line, 'APP_HOST=')) {
                $host = trim(substr($line, 9));
            }
        }
        if (!empty($port)) {
            return 'http://' . ($host === '0.0.0.0' ? '127.0.0.1' : $host) . ':' . $port;
        }
    }
    return 'http://127.0.0.1:8000';
}

if (!defined('AI_SCIENTIST_API')) {
    define('AI_SCIENTIST_API', get_bais_api_base_url());
}

function api_request(
    string $method,
    string $endpoint,
    ?array $data = null
): array {
    $url = AI_SCIENTIST_API . $endpoint;

    $ch = curl_init($url);

    $headers = [
        'Accept: application/json',
        'X-Client-Id: BAIS-WebUI',
    ];

    $options = [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_CONNECTTIMEOUT => 5,
        CURLOPT_TIMEOUT => 120,
        CURLOPT_CUSTOMREQUEST => $method,
        CURLOPT_HTTPHEADER => $headers,
    ];

    if ($data !== null) {
        $json = json_encode(
            $data,
            JSON_THROW_ON_ERROR
        );

        $headers[] = 'Content-Type: application/json';
        $options[CURLOPT_HTTPHEADER] = $headers;
        $options[CURLOPT_POSTFIELDS] = $json;
    }

    curl_setopt_array($ch, $options);

    $response = curl_exec($ch);

    if ($response === false) {
        $error = curl_error($ch);
        curl_close($ch);

        throw new RuntimeException(
            'FastAPI connection failed: ' . $error
        );
    }

    $httpStatus = curl_getinfo(
        $ch,
        CURLINFO_HTTP_CODE
    );

    curl_close($ch);

    if ($httpStatus === 204 || trim($response) === '') {
        return [];
    }

    $decoded = json_decode(
        $response,
        true,
        512,
        JSON_THROW_ON_ERROR
    );

    if ($httpStatus >= 400) {
        $detail = $decoded['detail'] ?? 'API request failed';
        if (is_array($detail)) {
            $errParts = [];
            foreach ($detail as $err) {
                if (is_array($err) && isset($err['msg'])) {
                    $loc = isset($err['loc']) && is_array($err['loc']) ? implode(' -> ', $err['loc']) . ': ' : '';
                    $errParts[] = $loc . $err['msg'];
                } else {
                    $errParts[] = is_string($err) ? $err : json_encode($err);
                }
            }
            $message = implode('; ', $errParts);
        } else {
            $message = (string)$detail;
        }

        throw new RuntimeException(
            "FastAPI returned HTTP {$httpStatus}: {$message}"
        );
    }

    return $decoded;
}

function api_get(string $endpoint): array
{
    return api_request(
        'GET',
        $endpoint
    );
}

function api_post(
    string $endpoint,
    array $data = []
): array {
    return api_request(
        'POST',
        $endpoint,
        $data
    );
}

function api_post_empty(string $endpoint): array
{
    return api_request(
        'POST',
        $endpoint
    );
}

function api_put(
    string $endpoint,
    array $data
): array {
    return api_request(
        'PUT',
        $endpoint,
        $data
    );
}

function api_patch(
    string $endpoint,
    ?array $data = null
): array {
    return api_request(
        'PATCH',
        $endpoint,
        $data
    );
}

function api_delete(
    string $endpoint
): array {
    return api_request(
        'DELETE',
        $endpoint
    );
}
