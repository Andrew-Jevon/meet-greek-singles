<?php
// Realistic search-shape SQL probe — runs the FULL search query Users_List
// would build (with WHERE clauses mimicking search_results.php), with the
// match_score injection in the SELECT and ORDER BY. Catches any subtle SQL
// errors that wouldn't show up in our isolated MatchScore unit tests.
//
// Sets a test viewer's onboarding answers temporarily, populates 3 candidate
// users with varied answers, runs the search, restores everything.

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

echo "REALISTIC SEARCH-SHAPE SQL PROBE\n";
echo "================================\n\n";

// Pick viewer + 3 candidates
$viewer = 1;
$candR = $dbh->query("SELECT user_id FROM userinfo WHERE user_id != $viewer ORDER BY user_id ASC LIMIT 3");
$cands = [];
while ($r = $candR->fetch_assoc()) $cands[] = (int)$r['user_id'];

if (count($cands) < 3) exit("Not enough test candidates\n");

// Snapshot
$snap = function($uid) use ($dbh) {
    return $dbh->query("SELECT looking_for, culture_importance, greek_meaning, relocation_openness FROM userinfo WHERE user_id=$uid")->fetch_assoc();
};
$origs = [$viewer => $snap($viewer)];
foreach ($cands as $c) $origs[$c] = $snap($c);

// Set viewer
$dbh->query("UPDATE userinfo SET looking_for=1, culture_importance=1, greek_meaning=47, relocation_openness=4 WHERE user_id=$viewer");
echo "Viewer (uid=$viewer) — looking_for=1, culture=1, greek_meaning=47 (5 bits set), relocation=4 (Maybe)\n\n";

// Set candidates with deliberately different scores
$labels = [
    $cands[0] => ['Near-perfect match', 1, 1, 47, 4],   // expect ~100
    $cands[1] => ['Friendship-first',   5, 1, 47, 4],   // expect ~64
    $cands[2] => ['Distant culture',    1, 5, 16, 1],   // expect lower
];
foreach ($labels as $uid => $vals) {
    list(, $l, $c, $g, $r) = $vals;
    $dbh->query("UPDATE userinfo SET looking_for=$l, culture_importance=$c, greek_meaning=$g, relocation_openness=$r WHERE user_id=$uid");
}

// Build the realistic search SQL — mirrors what search_results.php +
// Users_List would emit on the impact theme.
$scoreSql = MatchScore::buildScoreSql($viewer);
$whereCore = "u.active = 1 AND u.ban_global = 0 AND u.user_id != $viewer";

// Note: country/state live on the user table, not userinfo (i alias).
// Probe selects only the columns we actually need.
$searchSql = "
    SELECT u.user_id, u.name, u.gender, u.last_visit, u.country, u.state,
           i.looking_for, i.culture_importance, i.greek_meaning, i.relocation_openness,
           ($scoreSql) AS match_score
      FROM `user` u
      JOIN userinfo i ON i.user_id = u.user_id
     WHERE $whereCore
     ORDER BY match_score DESC, u.last_visit DESC
     LIMIT 25
";

echo "Generated search SQL (head):\n";
echo "----------------------------\n";
echo substr($searchSql, 0, 500) . "...\n\n";

echo "Executing — does it run without error?\n";
$res = $dbh->query($searchSql);
if (!$res) {
    echo "  FAIL: " . $dbh->error . "\n";
    exit;
}
echo "  OK — " . $res->num_rows . " rows returned\n\n";

echo "Top 10 results (sorted by match_score DESC):\n";
echo "--------------------------------------------\n";
printf("  %-5s  %-22s  %5s  %-3s %-3s %-3s %-3s  %s\n",
    "uid", "name", "score", "L", "C", "G", "R", "label");
$i = 0;
while ($row = $res->fetch_assoc()) {
    $i++;
    $uid = (int)$row['user_id'];
    $label = isset($labels[$uid]) ? $labels[$uid][0] : '';
    printf("  %-5d  %-22s  %5.1f  %-3d %-3d %-3d %-3d  %s\n",
        $uid, substr($row['name']??'', 0, 22), (float)$row['match_score'],
        (int)$row['looking_for'], (int)$row['culture_importance'],
        (int)$row['greek_meaning'], (int)$row['relocation_openness'],
        $label);
    if ($i >= 10) break;
}

echo "\nSORT ORDER VERIFICATION:\n";
$res->data_seek(0);
$prev = null;
$ok = true;
while ($row = $res->fetch_assoc()) {
    $s = (float)$row['match_score'];
    if ($prev !== null && $s > $prev) {
        echo "  FAIL: match_score $s > previous $prev (sort broken)\n";
        $ok = false;
    }
    $prev = $s;
}
if ($ok) echo "  OK — match_score is monotonically non-increasing across all rows\n";

// Verify our 3 known candidates ranked the way we expect
echo "\nEXPECTATION CHECK:\n";
$res->data_seek(0);
$ranks = [];
$rank = 0;
while ($row = $res->fetch_assoc()) {
    $rank++;
    $uid = (int)$row['user_id'];
    if (isset($labels[$uid])) {
        $ranks[$uid] = ['rank'=>$rank, 'score'=>(float)$row['match_score'], 'label'=>$labels[$uid][0]];
    }
}
foreach ($cands as $uid) {
    if (isset($ranks[$uid])) {
        echo "  uid=$uid ({$ranks[$uid]['label']})  rank #{$ranks[$uid]['rank']}  score={$ranks[$uid]['score']}\n";
    }
}
// Near-perfect should rank above friendship-first which should rank above distant
$np = $ranks[$cands[0]] ?? null;
$ff = $ranks[$cands[1]] ?? null;
$dc = $ranks[$cands[2]] ?? null;
if ($np && $ff && $dc) {
    if ($np['score'] > $ff['score'] && $ff['score'] > $dc['score']) {
        echo "  OK — near-perfect > friendship-first > distant ✓\n";
    } else {
        echo "  FAIL — expected ordering not preserved\n";
    }
}

// Restore everything
foreach ($origs as $uid => $row) {
    $l = (int)($row['looking_for'] ?? 0);
    $c = (int)($row['culture_importance'] ?? 0);
    $g = (int)($row['greek_meaning'] ?? 0);
    $r = (int)($row['relocation_openness'] ?? 0);
    $dbh->query("UPDATE userinfo SET looking_for=$l, culture_importance=$c, greek_meaning=$g, relocation_openness=$r WHERE user_id=$uid");
}
echo "\n  (all userinfo rows restored)\n\nDONE\n";
$dbh->close();
