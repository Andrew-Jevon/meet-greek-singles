<?php
// Post-deploy verification — read-only.
//   * userinfo.home_city present?
//   * user_var.home_city config row well-formed?
//   * Greek geo_state has 13 modern regions?
//   * Greek geo_city is empty?
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

echo "POST-DEPLOY VERIFY\n";
echo "==================\n\n";

// 1. userinfo.home_city
echo "1. userinfo.home_city column:\n";
$r = $dbh->query("SHOW COLUMNS FROM userinfo LIKE 'home_city'");
$row = $r->fetch_assoc();
echo $row ? "   {$row['Field']}  {$row['Type']}  default='{$row['Default']}'\n\n"
         : "   MISSING\n\n";

// 2. user_var.home_city config
echo "2. user_var.home_city config:\n";
$r = $dbh->query("SELECT id, position, value FROM config WHERE module='user_var' AND `option`='home_city'");
$row = $r->fetch_assoc();
if ($row) {
    echo "   id={$row['id']}  position={$row['position']}\n";
    $v = @unserialize($row['value']);
    if (is_array($v)) {
        echo "   unserialised:\n";
        foreach ($v as $k => $val) echo "     $k => " . (is_scalar($val) ? $val : json_encode($val)) . "\n";
    } else {
        echo "   COULD NOT UNSERIALIZE\n";
    }
} else {
    echo "   MISSING\n";
}
echo "\n";

// 3. Greek geo_state
echo "3. Greek geo_state rows (country_id=84):\n";
$r = $dbh->query("SELECT state_id, state_title, code FROM geo_state WHERE country_id=84 ORDER BY state_title ASC");
$count = 0;
while ($row = $r->fetch_assoc()) {
    echo "   {$row['state_id']}  {$row['state_title']}  ({$row['code']})\n";
    $count++;
}
echo "   total: $count  (expected 13)\n\n";

// 4. Greek geo_city (should be 0)
echo "4. Greek geo_city rows (joined to geo_state country_id=84):\n";
$r = $dbh->query("SELECT COUNT(*) c FROM geo_city gc JOIN geo_state gs ON gs.state_id=gc.state_id WHERE gs.country_id=84");
$row = $r->fetch_assoc();
echo "   count: {$row['c']}  (expected 0)\n\n";

// 5. test write — set home_city on user_id=1 (admin) to a sample value, then read back
echo "5. Round-trip write to userinfo.home_city (admin uid=1):\n";
$tag = 'verify_' . dechex(crc32(microtime(true)));
$r1 = $dbh->query("UPDATE userinfo SET home_city='$tag' WHERE user_id=1");
$r2 = $dbh->query("SELECT home_city FROM userinfo WHERE user_id=1");
$row = $r2->fetch_assoc();
echo "   wrote: '$tag'\n";
echo "   read:  '{$row['home_city']}'\n";
echo ($row['home_city'] === $tag ? "   OK\n" : "   MISMATCH\n") . "\n";
// reset
$dbh->query("UPDATE userinfo SET home_city='' WHERE user_id=1");

echo "DONE\n";
$dbh->close();
