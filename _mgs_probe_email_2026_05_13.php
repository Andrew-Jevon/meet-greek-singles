<?php
// Diagnose the email-sending pipeline: SMTP config, mail queue / log tables,
// PHP mail function availability, last server error_log entries.
set_time_limit(0); @ini_set('display_errors', 1);
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }
$g = array(); require __DIR__ . '/_include/config/db.php';
$d = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
$d->set_charset('utf8mb4');
header('Content-Type: text/plain');

echo "== PHP mail() function ==\n";
echo "  function_exists('mail'): " . (function_exists('mail') ? 'yes' : 'NO') . "\n";
echo "  sendmail_path: " . ini_get('sendmail_path') . "\n";
echo "  SMTP: " . ini_get('SMTP') . "\n";
echo "  smtp_port: " . ini_get('smtp_port') . "\n";

echo "\n== config rows relevant to email / smtp / mail ==\n";
$r = $d->query("SELECT id, module, `option`, CHAR_LENGTH(value) AS vl, type FROM `config`
                WHERE `option` LIKE '%mail%' OR `option` LIKE '%smtp%' OR module LIKE '%mail%' OR module LIKE '%smtp%'
                ORDER BY module, position");
while ($r && $row = $r->fetch_assoc()) {
    printf("  id=%-4s module=%-30s option=%-40s vlen=%-4s type=%s\n",
        $row['id'], $row['module'], $row['option'], $row['vl'], $row['type']);
}

echo "\n== config rows whose VALUE looks like an SMTP host or password is non-empty ==\n";
$r = $d->query("SELECT id, module, `option`, value, type FROM `config`
                WHERE (type='password' OR `option` LIKE '%smtp%' OR `option` LIKE 'host_%' OR `option` LIKE '%mail_%' OR module='smtp' OR module='email_send')
                ORDER BY module, position");
while ($r && $row = $r->fetch_assoc()) {
    // censor anything that looks like a credential
    $v = (string) $row['value'];
    if ($row['type'] === 'password') {
        $v = $v === '' ? '(empty)' : '(' . strlen($v) . ' chars, hidden)';
    } elseif (strlen($v) > 60) {
        $v = substr($v, 0, 60) . '... (' . strlen($v) . ' chars total)';
    }
    printf("  id=%-4s module=%-22s option=%-32s value=%s\n", $row['id'], $row['module'], $row['option'], $v);
}

echo "\n== Tables matching 'mail' / 'email' / 'queue' ==\n";
$r = $d->query("SHOW TABLES LIKE '%mail%'");
while ($r && ($row = $r->fetch_row())) echo "  " . $row[0] . "\n";
$r = $d->query("SHOW TABLES LIKE '%email%'");
while ($r && ($row = $r->fetch_row())) echo "  " . $row[0] . "\n";
$r = $d->query("SHOW TABLES LIKE '%queue%'");
while ($r && ($row = $r->fetch_row())) echo "  " . $row[0] . "\n";

echo "\n== email_auto_settings (Chameleon's auto-mail config) ==\n";
$r = $d->query("SELECT id, `option`, value FROM email_auto_settings");
if ($r) {
    while ($row = $r->fetch_assoc()) {
        $v = $row['value'];
        if (strlen($v) > 80) $v = substr($v, 0, 80) . '...';
        printf("  id=%s option=%s value=%s\n", $row['id'], $row['option'], $v);
    }
}

echo "\n== email_auto (full template list) ==\n";
$r = @$d->query("SHOW COLUMNS FROM email_auto");
if ($r) {
    $cols = array();
    while ($row = $r->fetch_assoc()) { $cols[] = $row['Field']; }
    echo "  columns: " . implode(', ', $cols) . "\n";
    $r2 = $d->query("SELECT id, name FROM email_auto ORDER BY id");
    while ($r2 && $row = $r2->fetch_assoc()) {
        echo "  id=" . $row['id'] . "  name=" . $row['name'] . "\n";
    }
}

echo "\n== Mail queue tables (if any) ==\n";
foreach (['email_queue', 'mail_queue', 'mail_log', 'email_log'] as $t) {
    $r = $d->query("SHOW TABLES LIKE '$t'");
    if ($r && $r->num_rows) {
        $r2 = $d->query("SELECT COUNT(*) c FROM `$t`");
        echo "  $t exists, rowcount=" . $r2->fetch_assoc()['c'] . "\n";
        $r3 = $d->query("SHOW COLUMNS FROM `$t`");
        while ($r3 && $row = $r3->fetch_assoc()) echo "    {$row['Field']}  {$row['Type']}\n";
    }
}

echo "\n== Tail of /error_log (if readable) ==\n";
$elog = __DIR__ . '/error_log';
if (is_readable($elog)) {
    $size = filesize($elog);
    echo "  size=$size bytes\n";
    $fp = fopen($elog, 'r');
    if ($fp) {
        if ($size > 8192) fseek($fp, $size - 8192);
        $tail = fread($fp, 8192);
        fclose($fp);
        // Show only last 80 lines max
        $lines = explode("\n", $tail);
        $lines = array_slice($lines, -80);
        foreach ($lines as $ln) echo "  $ln\n";
    }
} else {
    echo "  not readable\n";
}

echo "\nDONE\n";
$d->close();
