<?php
// Transient SQL query runner — token-protected.
set_time_limit(0);
@ini_set('display_errors', 1);
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }
$f = $_GET['f'] ?? '';
if (!preg_match('/^[A-Za-z0-9_.\-]+\.sql$/', $f)) { http_response_code(400); exit("bad\n"); }
$path = __DIR__ . '/' . $f;
if (!file_exists($path)) { http_response_code(404); exit("missing: $f\n"); }
$g = array(); require __DIR__ . '/_include/config/db.php';
$m = @new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
if ($m->connect_errno) { http_response_code(500); exit("connfail: " . $m->connect_error); }
$m->set_charset('utf8mb4');
header('Content-Type: text/plain');
$sql = trim(file_get_contents($path), "; \n\r\t");
$res = $m->query($sql);
if (!$res) { exit("query err: " . $m->error); }
if ($res === true) { echo "OK rows: " . $m->affected_rows; exit; }
$cols = array(); $first = true;
while ($row = $res->fetch_assoc()) {
    if ($first) { echo implode("\t", array_keys($row)) . "\n"; $first = false; }
    echo implode("\t", array_map(fn($v) => $v === null ? 'NULL' : $v, $row)) . "\n";
}
$res->free(); $m->close();
