<?php
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }
header('Content-Type: text/plain');
$f = '/tmp/mgs_gate.log';
if (file_exists($f)) {
    echo file_get_contents($f);
    if (isset($_GET['clear'])) @unlink($f);
} else {
    echo "(empty)";
}
