<?php
// Transient SQL runner. Reads db.php, connects, executes a .sql file.
// ?token=<hex>&f=<sql_file>
set_time_limit(0);
@ini_set('memory_limit', '512M');
@ini_set('display_errors', 1);
error_reporting(E_ALL);

$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) {
    http_response_code(403); exit("forbidden\n");
}

$f = $_GET['f'] ?? '';
if (!preg_match('/^[A-Za-z0-9_.\-]+\.sql$/', $f)) {
    http_response_code(400); exit("bad_file\n");
}

$path = __DIR__ . '/' . $f;
if (!file_exists($path)) {
    http_response_code(404); exit("sql_not_found: $f\n");
}

// Load DB config from Chameleon's db.php
$g = array();
require __DIR__ . '/_include/config/db.php';

$host = $g['db']['host'] ?? 'localhost';
$db   = $g['db']['db']   ?? '';
$user = $g['db']['user'] ?? '';
$pass = $g['db']['password'] ?? '';

$mysqli = @new mysqli($host, $user, $pass, $db);
if ($mysqli->connect_errno) {
    http_response_code(500);
    exit("connect_fail: {$mysqli->connect_error} (host=$host db=$db user=$user)\n");
}
$mysqli->set_charset('utf8mb4');

$sql = file_get_contents($path);

// Split on semicolons at line ends (naive — works for our simple migrations)
// Strip line comments ("-- ...") and block comments first
$sql = preg_replace('/\/\*.*?\*\//s', '', $sql);
$sql = preg_replace('/^\s*--.*$/m', '', $sql);

// Split into statements
$statements = array();
$buf = '';
foreach (explode("\n", $sql) as $line) {
    $buf .= $line . "\n";
    if (rtrim(rtrim($line), " \t") === '' || !preg_match('/;\s*$/', rtrim($line))) {
        if (!preg_match('/;\s*$/', rtrim($buf))) continue;
    }
    $trim = trim($buf);
    if ($trim !== '' && $trim !== ';') {
        $statements[] = $trim;
    }
    $buf = '';
}

header('Content-Type: text/plain');
$ok = 0; $err = 0; $errors = array();
foreach ($statements as $i => $stmt) {
    // Remove trailing ;
    $stmt = rtrim($stmt, "; \t\n\r");
    if ($stmt === '') continue;
    if ($mysqli->multi_query($stmt)) {
        do {
            if ($result = $mysqli->store_result()) {
                $result->free();
            }
        } while ($mysqli->more_results() && $mysqli->next_result());
        if ($mysqli->errno) {
            $err++;
            $errors[] = "Statement #{$i}: " . $mysqli->error . "\n  " . substr($stmt, 0, 120);
        } else {
            $ok++;
        }
    } else {
        $err++;
        $errors[] = "Statement #{$i}: " . $mysqli->error . "\n  " . substr($stmt, 0, 120);
    }
}

echo "OK\n";
echo "file: $f\n";
echo "host: $host  db: $db  user: $user\n";
echo "statements_ok: $ok\n";
echo "statements_err: $err\n";
if ($err) {
    echo "errors:\n";
    foreach ($errors as $e) echo "  " . $e . "\n";
}
$mysqli->close();
