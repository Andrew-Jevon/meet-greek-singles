<?php
// Diagnose why /administration/ login fails for an admin=1 user with a valid
// bcrypt password. Lists administration/ contents, looks at the auth code
// path, dumps the test admin's row and column types.
set_time_limit(0); @ini_set('display_errors', 1);
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }
$g = array(); require __DIR__ . '/_include/config/db.php';
$d = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
$d->set_charset('utf8mb4');
header('Content-Type: text/plain');

echo "== uid=1 + uid=63 (testadmin) ==\n";
$r = $d->query("SELECT user_id, name, mail, admin, role, active, ban_global, active_code, LEFT(password,4) AS pw_prefix, CHAR_LENGTH(password) AS pw_len FROM `user`");
while ($row = $r->fetch_assoc()) {
    printf("  uid=%-3s name=%-22s admin=%s role=%-12s active=%s ban=%s ac=%s pw=%s len=%s\n",
        $row['user_id'], $row['name'], $row['admin'], $row['role'], $row['active'],
        $row['ban_global'], ($row['active_code'] === '' ? '(empty)' : 'SET'),
        $row['pw_prefix'], $row['pw_len']);
}

echo "\n== administration/ directory listing ==\n";
$adm = __DIR__ . '/administration';
if (is_dir($adm)) {
    foreach (scandir($adm) as $f) {
        if ($f === '.' || $f === '..') continue;
        $full = $adm . '/' . $f;
        $sz = is_file($full) ? filesize($full) : '<dir>';
        echo "  $f  $sz\n";
    }
} else {
    echo "  NOT a directory\n";
}

echo "\n== admin.php (root) contents ==\n";
$ap = __DIR__ . '/admin.php';
if (is_readable($ap)) {
    echo file_get_contents($ap);
}

echo "\n== Look for password / login handling in administration/ ==\n";
if (is_dir($adm)) {
    foreach (scandir($adm) as $f) {
        if (substr($f, -4) !== '.php') continue;
        $body = @file_get_contents($adm . '/' . $f);
        $hits = array();
        foreach (['password_verify', 'md5', 'sha1', 'password_hash', 'is_admin', "admin'", 'admin =', '_login', 'incorrect', '$_POST'] as $needle) {
            if ($body && strpos($body, $needle) !== false) $hits[] = $needle;
        }
        if ($hits) echo "  $f  hits: " . implode(', ', $hits) . "\n";
    }
}

echo "\n== Search _include/ recursively for 'Login incorrect' or 'incorrect_login' ==\n";
function search_dir($base, $needle, &$found) {
    if (!is_dir($base)) return;
    foreach (scandir($base) as $f) {
        if ($f === '.' || $f === '..') continue;
        $p = $base . '/' . $f;
        if (is_dir($p)) { search_dir($p, $needle, $found); }
        elseif (substr($f, -4) === '.php' || substr($f, -4) === '.htm' || substr($f, -5) === '.html' || substr($f, -4) === '.tpl') {
            $body = @file_get_contents($p);
            if ($body !== false && stripos($body, $needle) !== false) {
                $found[] = $p;
            }
        }
    }
}
$found = array();
search_dir(__DIR__ . '/administration', 'incorrect', $found);
search_dir(__DIR__ . '/_include',       'incorrect', $found);
search_dir(__DIR__ . '/_lang',          'incorrect', $found);
search_dir(__DIR__ . '/_frameworks',    'incorrect', $found);
foreach ($found as $p) {
    echo "  FOUND: " . str_replace(__DIR__, '', $p) . "\n";
}

echo "\n== /administration/index.php first 200 lines ==\n";
$ip = $adm . '/index.php';
if (is_readable($ip)) {
    $lines = file($ip);
    foreach (array_slice($lines, 0, 200) as $i => $ln) {
        echo str_pad($i + 1, 4) . ' ' . rtrim($ln) . "\n";
    }
}

echo "\nDONE\n";
$d->close();
