<?php
@ini_set('display_errors', 1);
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }
$g = array(); require __DIR__ . '/_include/config/db.php';
$d = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
header('Content-Type: text/plain');
echo "Admin user check:\n";
$r = $d->query("SELECT user_id, name, mail, password, admin, active, ban_global FROM `user` WHERE user_id=1 OR name='admin' LIMIT 5");
while ($r && $row = $r->fetch_assoc()) {
    echo "  uid={$row['user_id']}  name='{$row['name']}'  mail='{$row['mail']}'  password='{$row['password']}'  admin={$row['admin']}  active={$row['active']}  ban={$row['ban_global']}\n";
}
echo "\nMD5 of 'AdminR@1!':  " . md5('AdminR@1!') . "\n";
