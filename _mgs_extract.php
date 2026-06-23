<?php
// Transient tar-extract script for staging deployment.
// Uploaded, invoked per-tar via HTTPS, then deleted.
// ?t=<tar_filename>&d=<subdir> → extract <tar> into <subdir> (relative to this file)
// ?t=<tar_filename>         → extract <tar> into webroot
// ?token=<hex>              → simple shared-secret auth

set_time_limit(0);
@ini_set('memory_limit', '1024M');
@ini_set('display_errors', 1);
error_reporting(E_ALL);

$EXPECTED_TOKEN = '977bf4ecc02e2de7003bb76881e9f686';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) {
    http_response_code(403);
    exit("forbidden\n");
}

$t = $_GET['t'] ?? '';
$d = $_GET['d'] ?? '';
if (!preg_match('/^[A-Za-z0-9_.\-]+\.tar$/', $t)) {
    http_response_code(400); exit("bad_tar\n");
}
if ($d !== '' && !preg_match('/^[A-Za-z0-9_.\-\/]+$/', $d)) {
    http_response_code(400); exit("bad_subdir\n");
}

$ROOT = __DIR__;
$tarPath = $ROOT . '/' . $t;
$target  = ($d === '') ? $ROOT : ($ROOT . '/' . $d);

if (!file_exists($tarPath)) { http_response_code(404); exit("tar_not_found: $t\n"); }
if (!is_dir($target)) {
    if (!@mkdir($target, 0755, true)) { http_response_code(500); exit("cant_mkdir: $d\n"); }
}

$start = microtime(true);
try {
    $phar = new PharData($tarPath);
    $phar->extractTo($target, null, true); // overwrite
} catch (Throwable $e) {
    http_response_code(500);
    exit("extract_fail: " . $e->getMessage() . "\n");
}

header('Content-Type: text/plain');
echo "OK\n";
echo "tar: $t\n";
echo "target: $d\n";
echo "seconds: " . round(microtime(true) - $start, 2) . "\n";
echo "tar_size: " . filesize($tarPath) . "\n";
