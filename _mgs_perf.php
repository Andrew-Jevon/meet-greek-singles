<?php
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }
header('Content-Type: text/plain');

echo "PHP " . PHP_VERSION . "\n";
echo "----\n";
echo "opcache.enable=" . ini_get('opcache.enable') . "\n";
echo "opcache.memory_consumption=" . ini_get('opcache.memory_consumption') . "\n";
echo "opcache.max_accelerated_files=" . ini_get('opcache.max_accelerated_files') . "\n";
echo "opcache.revalidate_freq=" . ini_get('opcache.revalidate_freq') . "\n";
echo "opcache.validate_timestamps=" . ini_get('opcache.validate_timestamps') . "\n";

if (function_exists('opcache_get_status')) {
    $s = @opcache_get_status(false);
    if ($s) {
        echo "----\n";
        echo "cache_full=" . var_export($s['cache_full'] ?? null, true) . "\n";
        echo "memory_usage.used_memory=" . number_format($s['memory_usage']['used_memory'] ?? 0) . "\n";
        echo "memory_usage.free_memory=" . number_format($s['memory_usage']['free_memory'] ?? 0) . "\n";
        $stats = $s['opcache_statistics'] ?? array();
        echo "stats.num_cached_scripts=" . ($stats['num_cached_scripts'] ?? 'n/a') . "\n";
        echo "stats.num_cached_keys=" . ($stats['num_cached_keys'] ?? 'n/a') . "\n";
        echo "stats.hits=" . number_format($stats['hits'] ?? 0) . "\n";
        echo "stats.misses=" . number_format($stats['misses'] ?? 0) . "\n";
        echo "stats.opcache_hit_rate=" . round($stats['opcache_hit_rate'] ?? 0, 2) . "%\n";
    } else {
        echo "opcache_get_status returned false (probably restricted)\n";
    }
}

echo "----\n";
echo "memory_limit=" . ini_get('memory_limit') . "\n";
echo "max_execution_time=" . ini_get('max_execution_time') . "\n";
echo "realpath_cache_size=" . ini_get('realpath_cache_size') . "\n";
echo "----\n";
$start = microtime(true);
$g = array(); require __DIR__ . '/_include/config/db.php';
$m = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
echo "mysqli connect time: " . round((microtime(true) - $start) * 1000, 2) . " ms\n";
$start = microtime(true);
$r = $m->query("SELECT COUNT(*) c FROM config");
$row = $r->fetch_assoc();
echo "SELECT COUNT(*) FROM config: " . round((microtime(true) - $start) * 1000, 2) . " ms (rows=" . $row['c'] . ")\n";
$m->close();
