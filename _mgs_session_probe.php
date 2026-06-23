<?php
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }
session_start();
header('Content-Type: text/plain');
echo "SESSION KEYS: \n";
foreach ($_SESSION as $k => $v) {
    if (is_scalar($v)) echo "  $k = " . substr((string)$v, 0, 80) . "\n";
    else echo "  $k = (" . gettype($v) . ")\n";
}
