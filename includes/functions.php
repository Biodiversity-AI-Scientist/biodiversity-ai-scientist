<?php

declare(strict_types=1);

if (!function_exists('mb_strimwidth')) {
    function mb_strimwidth(string $string, int $start, int $width, string $trimmarker = ''): string
    {
        if (strlen($string) <= $width) {
            return $string;
        }
        $cutLength = max(0, $width - strlen($trimmarker));
        return substr($string, $start, $cutLength) . $trimmarker;
    }
}

if (!function_exists('mb_strtolower')) {
    function mb_strtolower(string $string, string $encoding = 'UTF-8'): string
    {
        return strtolower($string);
    }
}

if (!function_exists('mb_strtoupper')) {
    function mb_strtoupper(string $string, string $encoding = 'UTF-8'): string
    {
        return strtoupper($string);
    }
}

if (!function_exists('mb_strlen')) {
    function mb_strlen(string $string, string $encoding = 'UTF-8'): int
    {
        return strlen($string);
    }
}


function truncateText(?string $str, int $maxLength = 40, string $marker = '...'): string
{
    $s = $str ?? '';
    return mb_strimwidth($s, 0, $maxLength, $marker);
}

function h(?string $value): string
{
    return htmlspecialchars(
        $value ?? '',
        ENT_QUOTES,
        'UTF-8'
    );
}

function getRequiredPositiveInt(string $name): int
{
    $value = filter_input(
        INPUT_GET,
        $name,
        FILTER_VALIDATE_INT
    );

    if ($value === false || $value === null || $value < 1) {
        throw new InvalidArgumentException(
            "Invalid {$name}."
        );
    }

    return $value;
}

function statusBadge(string $status): string
{
    return match ($status) {
        'active'       => 'bg-success',
        'pending'      => 'bg-secondary',
        'running'      => 'bg-warning text-dark',
        'completed'    => 'bg-success',
        'paused'       => 'bg-warning text-dark',
        'failed'       => 'bg-danger',
        'draft'        => 'bg-secondary',
        'proposed'     => 'bg-secondary',
        'open'         => 'bg-secondary',
        'under_review' => 'bg-warning text-dark',
        'approved'     => 'bg-success',
        'archived'     => 'bg-secondary text-white opacity-75',
        default        => 'bg-secondary',
    };
}
