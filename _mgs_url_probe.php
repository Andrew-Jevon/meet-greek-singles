<?php
// Probe /login URL routing — look in pages table and SEO/router tables
@ini_set('display_errors', 1);
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }

$g = array();
require __DIR__ . '/_include/config/db.php';
$dbh = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
if ($dbh->connect_errno) { exit("db: " . $dbh->connect_error); }
$dbh->set_charset('utf8mb4');
header('Content-Type: text/plain');

// Look for any pages table entry that might map /login
echo "=== pages table entries with title/url containing 'login' ===\n";
$r = $dbh->query("SHOW COLUMNS FROM pages");
$cols = [];
while ($r && $row = $r->fetch_assoc()) $cols[] = $row['Field'];
echo "  pages columns: " . implode(', ', $cols) . "\n\n";

$where = [];
foreach ($cols as $c) {
    if (in_array($c, ['title','seo_url','url','code','name','section'])) {
        $where[] = "`$c` LIKE '%login%'";
        $where[] = "`$c` LIKE '%forget%'";
        $where[] = "`$c` LIKE '%forgot%'";
    }
}
if ($where) {
    $sql = "SELECT * FROM pages WHERE " . implode(' OR ', $where) . " LIMIT 30";
    echo "  query: $sql\n\n";
    $r = $dbh->query($sql);
    while ($r && $row = $r->fetch_assoc()) {
        foreach ($row as $k => $v) echo "    $k = " . substr((string)$v, 0, 80) . "\n";
        echo "    ---\n";
    }
}

// Look for routing table or seo table
echo "\n=== seo table with url containing 'login' ===\n";
$r = $dbh->query("SELECT * FROM seo WHERE url LIKE '%login%' OR url LIKE '%forget%' LIMIT 10");
if ($r) {
    while ($row = $r->fetch_assoc()) {
        foreach ($row as $k => $v) echo "    $k = " . substr((string)$v, 0, 100) . "\n";
        echo "    ---\n";
    }
}

// page_seo table
echo "\n=== page_seo table (if exists) ===\n";
$r = $dbh->query("SHOW TABLES LIKE 'page_seo'");
if ($r && $r->num_rows > 0) {
    $r = $dbh->query("SELECT * FROM page_seo WHERE seo_url LIKE '%login%' OR seo_url LIKE '%forget%' LIMIT 10");
    while ($r && $row = $r->fetch_assoc()) {
        foreach ($row as $k => $v) echo "    $k = " . substr((string)$v, 0, 100) . "\n";
        echo "    ---\n";
    }
} else {
    echo "  (no page_seo table)\n";
}

$dbh->close();
