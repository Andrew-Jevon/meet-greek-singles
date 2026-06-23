<?php
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }
header('Content-Type: text/plain');

if (!function_exists('opcache_reset')) {
    echo "opcache_reset not available\n";
    if (function_exists('opcache_invalidate')) {
        $files = array(
            __DIR__ . '/_include/current/prelaunch.class.php',
            __DIR__ . '/_include/current/onboarding.class.php',
            __DIR__ . '/_include/current/common.class.php',
        );
        foreach ($files as $f) {
            $r = opcache_invalidate($f, true);
            echo "invalidate($f): " . var_export($r, true) . "\n";
        }
    }
} else {
    echo "opcache_reset(): " . var_export(opcache_reset(), true) . "\n";
}

echo "\n--- after reset ---\n";
$s = @opcache_get_status(false);
if ($s) {
    echo "num_cached_scripts = " . ($s['opcache_statistics']['num_cached_scripts'] ?? 'n/a') . "\n";
    echo "memory_used        = " . number_format($s['memory_usage']['used_memory'] ?? 0) . "\n";
}
