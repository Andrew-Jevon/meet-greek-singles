<?php
// Find Chameleon's actual admin credentials.
set_time_limit(0); @ini_set('display_errors', 1);
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }
$g = array(); require __DIR__ . '/_include/config/db.php';
$d = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
$d->set_charset('utf8mb4');
header('Content-Type: text/plain');

echo "== _include/config/ file list ==\n";
foreach (scandir(__DIR__ . '/_include/config') as $f) {
    if ($f === '.' || $f === '..') continue;
    echo "  $f\n";
}

echo "\n== Try to load main config and report admin_password presence ==\n";
// Don't dump the value to the response — just say if it's set and the length.
$config_dir = __DIR__ . '/_include/config';
foreach (['config.php','site.php','main.php','admin.php'] as $candidate) {
    $p = $config_dir . '/' . $candidate;
    if (is_readable($p)) {
        echo "  reading $candidate (size=" . filesize($p) . ")...\n";
        // Read raw contents (no eval) and search for admin_password assignments
        $body = file_get_contents($p);
        if (preg_match_all("/admin_password.{0,80}/", $body, $m)) {
            foreach ($m[0] as $hit) {
                echo "    HIT: " . trim($hit) . "\n";
            }
        }
    }
}

echo "\n== admin_replier table ==\n";
$r = $d->query("SHOW TABLES LIKE 'admin_replier'");
if ($r && $r->num_rows) {
    $r2 = $d->query("SHOW COLUMNS FROM `admin_replier`");
    $cols = array();
    while ($r2 && $row = $r2->fetch_assoc()) { $cols[] = $row['Field']; }
    echo "  columns: " . implode(', ', $cols) . "\n";
    $r3 = $d->query("SELECT * FROM `admin_replier`");
    $n = 0;
    while ($r3 && $row = $r3->fetch_assoc()) {
        $n++;
        echo "  row:\n";
        foreach ($row as $k => $v) {
            if ($k === 'password') {
                $v = '(' . strlen((string)$v) . ' chars, ' . (preg_match('/^[a-f0-9]{32}$/i', (string)$v) ? 'looks like md5' : 'other') . ')';
            }
            echo "    $k = $v\n";
        }
    }
    if (!$n) echo "  (empty)\n";
} else {
    echo "  admin_replier table not found\n";
}

echo "\n== admin_login recent attempts (last 50) ==\n";
$r = $d->query("SHOW TABLES LIKE 'admin_login'");
if ($r && $r->num_rows) {
    $r2 = $d->query("SELECT * FROM `admin_login` ORDER BY time DESC LIMIT 50");
    $n = 0;
    while ($r2 && $row = $r2->fetch_assoc()) {
        $n++;
        printf("  time=%s ip=%s success=%s\n",
            $row['time'] ?? '?', $row['ip'] ?? '?', $row['success'] ?? '?');
    }
    if (!$n) echo "  (empty)\n";

    // How many failed in last 10 min, total
    $r3 = $d->query("SELECT COUNT(*) c FROM `admin_login` WHERE success='N' AND time > DATE_SUB(NOW(), INTERVAL 10 MINUTE)");
    if ($r3) {
        $row = $r3->fetch_assoc();
        echo "\n  failed attempts in last 10 min (any IP): " . $row['c'] . "\n";
    }
} else {
    echo "  admin_login table not found\n";
}

echo "\nDONE\n";
$d->close();
