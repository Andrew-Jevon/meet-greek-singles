<?php
// Sets a temporary known password on a non-Irene test user, returns the
// snapshot for restore. Token-protected.
@ini_set('display_errors', 1);
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }
$g = array(); require __DIR__ . '/_include/config/db.php';
$d = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
header('Content-Type: text/plain');

// Pick uid=2 (acidrocker) — first non-Irene user. Snapshot password.
$row = $d->query("SELECT user_id, name, mail, password, admin FROM `user` WHERE user_id=2")->fetch_assoc();
if (!$row) exit("uid=2 not found\n");

echo "Test user:\n";
echo "  uid={$row['user_id']}  name='{$row['name']}'  mail='{$row['mail']}'  admin={$row['admin']}\n";
echo "  ORIGINAL_PASSWORD_HASH='" . $row['password'] . "'\n";

$mode = $_GET['mode'] ?? 'set';
$plain = 'mgsTest!2026';

if ($mode === 'set') {
    // Try BOTH bcrypt and md5 forms — Chameleon's encoded login may try one or
    // the other. We set bcrypt (the modern form prod uses).
    $hash = password_hash($plain, PASSWORD_BCRYPT);
    $d->query("UPDATE `user` SET password='" . $d->real_escape_string($hash) . "' WHERE user_id=2");
    echo "  set password to bcrypt hash of '$plain'\n";
} elseif ($mode === 'set_md5') {
    $hash = md5($plain);
    $d->query("UPDATE `user` SET password='$hash' WHERE user_id=2");
    echo "  set password to MD5 of '$plain'\n";
} elseif ($mode === 'restore') {
    $orig = $_GET['orig'] ?? '';
    if (!$orig) exit("missing &orig=...\n");
    $d->query("UPDATE `user` SET password='" . $d->real_escape_string($orig) . "' WHERE user_id=2");
    echo "  restored password to '$orig'\n";
}
$d->close();
