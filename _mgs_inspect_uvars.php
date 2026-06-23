<?php
// Read-only — dump the serialized value of every user_var config row, so we
// can see what keys text-type fields conventionally include.
@ini_set('display_errors', 1);
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }

$g = array();
require __DIR__ . '/_include/config/db.php';
$dbh = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
if ($dbh->connect_errno) { exit("db: " . $dbh->connect_error); }
$dbh->set_charset('utf8mb4');

header('Content-Type: text/plain');

$r = $dbh->query("SELECT `option`, value FROM config WHERE module='user_var' ORDER BY position ASC");
while ($row = $r->fetch_assoc()) {
    $v = @unserialize($row['value']);
    if (!is_array($v)) { echo "{$row['option']}: (not unserializable)\n\n"; continue; }
    $type = $v['type'] ?? '?';
    echo "=== {$row['option']}  (type=$type) ===\n";
    foreach ($v as $k => $val) {
        $vs = is_scalar($val) ? var_export($val, true) : json_encode($val);
        echo "  $k => $vs\n";
    }
    echo "\n";
}
$dbh->close();
