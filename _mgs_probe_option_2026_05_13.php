<?php
// Inspect the option table schema so we can insert a token_admin entry
// for the /administration/ login bypass.
set_time_limit(0); @ini_set('display_errors', 1);
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }
$g = array(); require __DIR__ . '/_include/config/db.php';
$d = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
$d->set_charset('utf8mb4');
header('Content-Type: text/plain');

echo "== Tables matching '%option%' ==\n";
$r = $d->query("SHOW TABLES LIKE '%option%'");
$tables = array();
while ($r && ($row = $r->fetch_row())) { $tables[] = $row[0]; echo "  " . $row[0] . "\n"; }
$r2 = $d->query("SHOW TABLES LIKE '%config%'");
while ($r2 && ($row = $r2->fetch_row())) { $tables[] = $row[0]; echo "  " . $row[0] . "\n"; }
$r3 = $d->query("SHOW TABLES LIKE '%setting%'");
while ($r3 && ($row = $r3->fetch_row())) { $tables[] = $row[0]; echo "  " . $row[0] . "\n"; }

foreach ($tables as $t) {
    echo "\n== columns of `$t` ==\n";
    $r = $d->query("SHOW COLUMNS FROM `$t`");
    while ($r && $row = $r->fetch_assoc()) {
        echo "  {$row['Field']}  {$row['Type']}\n";
    }
    echo "  rowcount: ";
    $r = $d->query("SELECT COUNT(*) c FROM `$t`");
    echo $r ? $r->fetch_assoc()['c'] : 'err';
    echo "\n";
}

echo "\n== Look for 'admin_password' or 'token_admin' in any of these tables ==\n";
foreach ($tables as $t) {
    // Get columns
    $r = $d->query("SHOW COLUMNS FROM `$t`");
    $cols = array();
    while ($r && $row = $r->fetch_assoc()) {
        if (preg_match('/^(varchar|text|char|tinytext|mediumtext|longtext)/i', $row['Type'])) {
            $cols[] = $row['Field'];
        }
    }
    foreach ($cols as $c) {
        $sql = "SELECT * FROM `$t` WHERE `$c` IN ('admin_password','token_admin') LIMIT 5";
        $r = @$d->query($sql);
        while ($r && $row = $r->fetch_assoc()) {
            echo "  match in $t (col=$c):\n";
            foreach ($row as $k => $v) {
                if (in_array($k, ['value','option_value','val'], true) && strlen((string)$v) > 4 && $row[$c] === 'admin_password') {
                    $v = '(' . strlen((string)$v) . ' chars, hidden)';
                }
                echo "    $k = " . substr((string)$v, 0, 80) . "\n";
            }
        }
    }
}

echo "\nDONE\n";
$d->close();
