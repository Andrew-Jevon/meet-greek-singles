<?php
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }
$f = $_GET['f'] ?? '';
if (!preg_match('|^[A-Za-z0-9_./\-]+$|', $f) || strpos($f, '..') !== false) { http_response_code(400); exit("bad\n"); }
$path = __DIR__ . '/' . $f;
if (!file_exists($path)) { http_response_code(404); exit("missing: $f"); }
header('Content-Type: text/plain');
echo "FILE: $f  (mtime=" . date('Y-m-d H:i:s', filemtime($path)) . ")\n";
echo "----\n";
echo file_get_contents($path);
