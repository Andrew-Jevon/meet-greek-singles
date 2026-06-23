<?php
// One-shot inspection — reports the state of geo_* and userinfo columns
// relevant to today's deploy. Read-only; safe to run repeatedly.
// Token-protected. Delete after.

set_time_limit(0);
@ini_set('display_errors', 1);
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }

$g = array();
require __DIR__ . '/_include/config/db.php';
$dbh = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
if ($dbh->connect_errno) { exit("db: " . $dbh->connect_error); }
$dbh->set_charset('utf8mb4');

header('Content-Type: text/plain');

echo "INSPECTION\n";
echo "==========\n\n";

// 1. geo_country schema (does it have country_code?)
echo "1. geo_country columns:\n";
$r = $dbh->query("SHOW COLUMNS FROM geo_country");
while ($r && $row = $r->fetch_assoc()) {
    echo "   {$row['Field']}  {$row['Type']}\n";
}
echo "\n";

// 2. Greece in geo_country (column is `code` per step 1, not country_code)
echo "2. Greece in geo_country (try code='GR' or title containing Greece/Hellas):\n";
$r = $dbh->query("SELECT country_id, country_title, code FROM geo_country
    WHERE code='GR' OR country_title LIKE '%Greece%' OR country_title LIKE '%Hellas%'
    LIMIT 5");
$gid = null;
if (!$r) {
    echo "   QUERY FAILED: " . $dbh->error . "\n";
} else {
    while ($row = $r->fetch_assoc()) {
        echo "   row: country_id={$row['country_id']}  title='{$row['country_title']}'  code='{$row['code']}'\n";
        if ($gid === null) $gid = (int) $row['country_id'];
    }
}
echo "   => country_id=" . ($gid ?? 'NOT FOUND') . "\n\n";

// 2b. Failback — dump first 20 country rows to eyeball if step 2 still empty
if (!$gid) {
    echo "2b. First 20 geo_country rows:\n";
    $r = $dbh->query("SELECT country_id, country_title, code FROM geo_country ORDER BY country_id ASC LIMIT 20");
    while ($r && $row = $r->fetch_assoc()) {
        echo "   {$row['country_id']}  '{$row['country_title']}'  ({$row['code']})\n";
    }
    echo "\n";
    // Also try direct grep on title
    echo "2c. Any title containing 'reece':\n";
    $r = $dbh->query("SELECT country_id, country_title, code FROM geo_country WHERE country_title LIKE '%reece%' LIMIT 10");
    while ($r && $row = $r->fetch_assoc()) {
        echo "   {$row['country_id']}  '{$row['country_title']}'  ({$row['code']})\n";
    }
    echo "\n";
}

// 3. Current Greek geo_state rows
if ($gid) {
    echo "3. Current geo_state rows for Greece (country_id=$gid):\n";
    $r = $dbh->query("SELECT state_id, state_title, code FROM geo_state WHERE country_id=$gid ORDER BY state_title ASC");
    $count = 0;
    while ($r && $row = $r->fetch_assoc()) {
        echo "   {$row['state_id']}  {$row['state_title']}  ({$row['code']})\n";
        $count++;
    }
    echo "   (total: $count)\n\n";

    // 4. geo_city rows attached to Greek states
    echo "4. geo_city rows attached to Greek states:\n";
    $r = $dbh->query("SELECT COUNT(*) c FROM geo_city gc JOIN geo_state gs ON gs.state_id=gc.state_id WHERE gs.country_id=$gid");
    $row = $r->fetch_assoc();
    echo "   count: {$row['c']}\n\n";
}

// 5. geo_state schema
echo "5. geo_state columns:\n";
$r = $dbh->query("SHOW COLUMNS FROM geo_state");
while ($r && $row = $r->fetch_assoc()) {
    echo "   {$row['Field']}  {$row['Type']}\n";
}
echo "\n";

// 6. userinfo.home_city existence?
echo "6. userinfo.home_city column:\n";
$r = $dbh->query("SELECT COUNT(*) c FROM information_schema.columns
    WHERE table_schema=DATABASE() AND table_name='userinfo' AND column_name='home_city'");
$row = $r->fetch_assoc();
echo "   exists: " . ($row['c'] > 0 ? "YES" : "NO") . "\n\n";

// 7. user_var.home_city existing config row?
echo "7. config row for user_var.home_city:\n";
$r = $dbh->query("SELECT id, position, length(value) as vlen FROM config WHERE module='user_var' AND `option`='home_city'");
$found = false;
while ($r && $row = $r->fetch_assoc()) {
    echo "   id={$row['id']}  position={$row['position']}  value_bytes={$row['vlen']}\n";
    $found = true;
}
if (!$found) echo "   not found (will be inserted)\n";
echo "\n";

// 8. user count (so we know how many existing rows would get '' default for home_city)
echo "8. user count:\n";
$r = $dbh->query("SELECT COUNT(*) c FROM user");
$row = $r->fetch_assoc();
echo "   total users: {$row['c']}\n\n";

echo "DONE\n";
$dbh->close();
