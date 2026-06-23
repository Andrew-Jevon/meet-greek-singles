<?php
// Read the just-registered E2E test user's home_city from userinfo.
// Token-protected.
@ini_set('display_errors', 1);
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }

$g = array();
require __DIR__ . '/_include/config/db.php';
$dbh = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
if ($dbh->connect_errno) { exit("db: " . $dbh->connect_error); }
$dbh->set_charset('utf8mb4');

header('Content-Type: text/plain');

echo "E2E persistence check\n";
echo "=====================\n\n";

// Recent test users (last 30 mins)
$r = $dbh->query("
    SELECT u.user_id, u.name, u.mail, u.register, u.country, u.state,
           ui.home_city
      FROM user u
      LEFT JOIN userinfo ui ON ui.user_id = u.user_id
     WHERE u.mail LIKE 'e2e_%@example.test'
        OR u.name LIKE 'e2etest%'
     ORDER BY u.register DESC
     LIMIT 5");
if ($r) {
    while ($row = $r->fetch_assoc()) {
        echo "  uid={$row['user_id']}  name='{$row['name']}'  mail='{$row['mail']}'\n";
        echo "    register={$row['register']}  country={$row['country']}  state={$row['state']}\n";
        echo "    home_city='{$row['home_city']}'\n\n";
    }
} else {
    echo "QUERY FAILED: " . $dbh->error . "\n";
}

// Run a LIKE search on home_city (mirrors search_results.php logic) to confirm
// the filter would pick this user up.
$needle = 'Athens';
echo "\nLIKE search on home_city '%$needle%':\n";
$r = $dbh->query("SELECT u.user_id, u.name, ui.home_city FROM user u
                  JOIN userinfo ui ON ui.user_id=u.user_id
                  WHERE ui.home_city LIKE '%$needle%' LIMIT 5");
$hits = 0;
while ($row = $r->fetch_assoc()) {
    echo "  uid={$row['user_id']}  name={$row['name']}  home_city='{$row['home_city']}'\n";
    $hits++;
}
echo "  ($hits hits)\n";

// Cleanup test users to keep the DB clean
echo "\nDeleting test users (mail like 'e2e_%@example.test')...\n";
$r1 = $dbh->query("SELECT user_id FROM user WHERE mail LIKE 'e2e_%@example.test'");
$ids = array();
while ($row = $r1->fetch_assoc()) $ids[] = (int) $row['user_id'];
if ($ids) {
    $idList = implode(',', $ids);
    $dbh->query("DELETE FROM user WHERE user_id IN ($idList)");
    $dbh->query("DELETE FROM userinfo WHERE user_id IN ($idList)");
    echo "  deleted " . count($ids) . " test users + their userinfo rows\n";
} else {
    echo "  (no test users to delete)\n";
}

echo "\nDONE\n";
$dbh->close();
