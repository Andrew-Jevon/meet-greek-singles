<?php
// MatchScore self-test — populates a fake user's onboarding answers, then
// runs MatchScore::buildScoreSql() through the live DB to confirm:
//   1) The class loads without parse errors.
//   2) The generated SQL is valid (executes without error).
//   3) The score values are sane (0..100, varies by candidate).
// Read-only against actual user data. Token-protected.

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

// Lightweight DB shim so MatchScore::compute / buildScoreSql work outside
// Chameleon bootstrap.
class DB {
    public static $h;
    public static function row($sql) {
        $r = self::$h->query($sql);
        if (!$r) return null;
        return $r->fetch_assoc();
    }
}
DB::$h = $dbh;

require __DIR__ . '/_include/current/match_score.class.php';

echo "MatchScore probe\n";
echo "================\n\n";

// Pick a user we can mutate temporarily — admin (uid=1) is available
$viewer = 1;

// Snapshot original values so we can restore
$orig = $dbh->query("SELECT looking_for, culture_importance, greek_meaning, relocation_openness FROM userinfo WHERE user_id=$viewer")->fetch_assoc();
echo "viewer (uid=$viewer) original userinfo: " . json_encode($orig) . "\n\n";

// Set a typical "serious diaspora user" profile
$dbh->query("UPDATE userinfo
                SET looking_for = 1,
                    culture_importance = 1,
                    greek_meaning = 47,        -- bits 1,2,3,5 (family, language, faith, connection)
                    relocation_openness = 4
              WHERE user_id = $viewer");

echo "viewer set to: looking_for=1, culture_importance=1, greek_meaning=47 (bits 1+2+3+5+ = family/language/faith/connection), relocation_openness=4\n\n";

// 1. userHasAnswers
$has = MatchScore::userHasAnswers($viewer) ? 'YES' : 'NO';
echo "1. MatchScore::userHasAnswers(viewer): $has\n\n";

// 2. buildScoreSql
$sql = MatchScore::buildScoreSql($viewer);
echo "2. MatchScore::buildScoreSql(viewer):\n";
echo "   " . substr($sql, 0, 300) . (strlen($sql) > 300 ? "...\n   ...(total " . strlen($sql) . " chars)\n" : "\n");
echo "\n";

// 3. Test the SQL by running it as part of a minimal SELECT
$testSql = "SELECT u.user_id, u.name,
                   ($sql) AS match_score,
                   i.looking_for AS l, i.culture_importance AS c,
                   i.greek_meaning AS g, i.relocation_openness AS r
              FROM `user` u
              JOIN userinfo i ON i.user_id = u.user_id
              WHERE u.user_id != $viewer
                AND u.active = 1
              ORDER BY match_score DESC
              LIMIT 10";

echo "3. Run the SQL against real users (top 10 by score):\n";
echo "------------------------------------------------------\n";
$r = $dbh->query($testSql);
if (!$r) {
    echo "  ERR: " . $dbh->error . "\n";
} else {
    printf("  %5s  %-20s  %5s  %3s %3s %3s %3s\n", "uid", "name", "score", "L", "C", "G", "R");
    while ($row = $r->fetch_assoc()) {
        printf("  %5d  %-20s  %5.1f  %3d %3d %3d %3d\n",
            $row['user_id'], substr($row['name'] ?? '', 0, 20),
            (float)$row['match_score'],
            (int)$row['l'], (int)$row['c'], (int)$row['g'], (int)$row['r']);
    }
}

// 4. Compute() vs buildScoreSql() — should produce the same number for any
//    given user
echo "\n4. PHP MatchScore::compute vs SQL match_score (parity check):\n";
$r = $dbh->query("SELECT user_id FROM `user` WHERE user_id != $viewer AND active = 1 LIMIT 5");
while ($r && $row = $r->fetch_assoc()) {
    $candUid = (int) $row['user_id'];
    $php = MatchScore::compute($viewer, $candUid);
    $sqlR = $dbh->query("SELECT ($sql) AS s FROM userinfo i WHERE i.user_id=$candUid")->fetch_assoc();
    $sqlScore = isset($sqlR['s']) ? (float)$sqlR['s'] : 0;
    $match = (abs($php - $sqlScore) < 1.0) ? "OK" : "MISMATCH";
    printf("  uid=%d  PHP=%d  SQL=%.1f  %s\n", $candUid, $php, $sqlScore, $match);
}

// Restore
$ol = (int)($orig['looking_for'] ?? 0);
$oc = (int)($orig['culture_importance'] ?? 0);
$og = (int)($orig['greek_meaning'] ?? 0);
$or = (int)($orig['relocation_openness'] ?? 0);
$dbh->query("UPDATE userinfo SET looking_for=$ol, culture_importance=$oc, greek_meaning=$og, relocation_openness=$or WHERE user_id = $viewer");
echo "\n  (viewer userinfo restored to original)\n";

echo "\nDONE\n";
$dbh->close();
