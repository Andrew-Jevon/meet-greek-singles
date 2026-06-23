<?php
@ini_set('display_errors', 1);
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }
$g = array(); require __DIR__ . '/_include/config/db.php';
$d = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
$d->set_charset('utf8mb4');
header('Content-Type: text/plain');

// Find email/confirm/active columns on user table
echo "== user table columns matching email/confirm/active/verify ==\n";
$r = $d->query("SHOW COLUMNS FROM `user`");
while ($r && $row = $r->fetch_assoc()) {
    $f = strtolower($row['Field']);
    if (strpos($f, 'mail') !== false || strpos($f, 'confirm') !== false
        || strpos($f, 'active') !== false || strpos($f, 'verif') !== false) {
        echo "  {$row['Field']}  {$row['Type']}  default=" . var_export($row['Default'], true) . "\n";
    }
}

echo "\n== Recent users + their email-related flag values ==\n";
$cols = ['user_id','name','mail','active','register'];
// Try also email_active / mail_active / mail_confirm if they exist
$r = $d->query("SELECT user_id, name, mail, active, register FROM `user` ORDER BY user_id DESC LIMIT 6");
printf("  %-4s  %-20s  %-30s  %-8s  %s\n", "uid", "name", "mail", "active", "register");
while ($r && $row = $r->fetch_assoc()) {
    printf("  %-4s  %-20s  %-30s  %-8s  %s\n",
        $row['user_id'], substr($row['name'], 0, 20), substr($row['mail'], 0, 30),
        $row['active'], $row['register']);
}

echo "\n== Try to find email_active / mail_active / mail_confirm on user table ==\n";
foreach (['email_active', 'mail_active', 'mail_confirm', 'mail_confirmed', 'is_email_confirmed', 'email_confirmed', 'mail_check', 'email_verified'] as $c) {
    $r = $d->query("SELECT COUNT(*) c FROM information_schema.columns
        WHERE table_schema=DATABASE() AND table_name='user' AND column_name='$c'");
    $n = (int) $r->fetch_assoc()['c'];
    echo "  $c → " . ($n > 0 ? "EXISTS" : "no") . "\n";
}

echo "\nDONE\n";
$d->close();
