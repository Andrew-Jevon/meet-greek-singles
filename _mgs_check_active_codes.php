<?php
@ini_set('display_errors', 1);
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }
$g = array(); require __DIR__ . '/_include/config/db.php';
$d = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
$d->set_charset('utf8mb4');
header('Content-Type: text/plain');

echo "== Total users + active_code state ==\n";
$r = $d->query("SELECT COUNT(*) c FROM user");
$total = $r->fetch_assoc()['c'];
echo "  total users: $total\n";

$r = $d->query("SELECT COUNT(*) c FROM user WHERE active_code != ''");
$pending = $r->fetch_assoc()['c'];
echo "  users with active_code set (unconfirmed): $pending\n";

$r = $d->query("SELECT COUNT(*) c FROM user WHERE active_code = ''");
$confirmed = $r->fetch_assoc()['c'];
echo "  users with active_code empty (confirmed): $confirmed\n\n";

echo "== Users still pending confirmation ==\n";
$r = $d->query("SELECT user_id, name, mail, active, active_code, register FROM user WHERE active_code != '' ORDER BY user_id ASC LIMIT 30");
while ($r && $row = $r->fetch_assoc()) {
    echo "  uid={$row['user_id']}  name={$row['name']}  mail={$row['mail']}  active={$row['active']}  code_len=" . strlen($row['active_code']) . "  reg={$row['register']}\n";
}

echo "\nDONE\n";
$d->close();
