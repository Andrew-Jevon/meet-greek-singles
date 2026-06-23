<?php
// MatchScore probe 2 — populate two users with non-zero answers, run scoring
// across multiple scenarios to confirm the weights produce sensible results.
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

// We need two users with userinfo rows. Use uid=1 (admin) as viewer, find
// a real candidate to mutate temporarily.
$viewer = 1;
$candR = $dbh->query("SELECT user_id FROM userinfo WHERE user_id != $viewer LIMIT 1");
$candUid = (int) $candR->fetch_assoc()['user_id'];

// Snapshot both
$origViewer = $dbh->query("SELECT looking_for, culture_importance, greek_meaning, relocation_openness FROM userinfo WHERE user_id=$viewer")->fetch_assoc();
$origCand   = $dbh->query("SELECT looking_for, culture_importance, greek_meaning, relocation_openness FROM userinfo WHERE user_id=$candUid")->fetch_assoc();

// Set viewer to a "diaspora seeking serious relationship" archetype.
$dbh->query("UPDATE userinfo SET looking_for=1, culture_importance=1, greek_meaning=47, relocation_openness=4 WHERE user_id=$viewer");

echo "MatchScore scenario probe\n";
echo "=========================\n\n";
echo "viewer (uid=$viewer): looking_for=1 (long-term), culture=1 (core), greek_meaning=47 (4 bits), relocation=4 (maybe)\n";
echo "candidate (uid=$candUid) tested across 6 scenarios:\n\n";

$scenarios = array(
    'Identical mirror'         => array(1, 1, 47, 4),
    'Same intent, +1 culture'  => array(1, 2, 47, 4),
    'Marriage instead'         => array(2, 1, 47, 4),
    'Friendship first'         => array(5, 1, 47, 4),
    'Different greek meaning'  => array(1, 1, 16, 4),  // bit 5 only (connection)
    'Wants to stay put'        => array(1, 1, 47, 5),  // No to relocating
);

printf("  %-30s  %5s  %5s  %s\n", "scenario (cand: l/c/g/r)", "PHP", "SQL", "match");
printf("  %-30s  %5s  %5s  %s\n", str_repeat('-', 30), '----', '----', '-----');
$sql = MatchScore::buildScoreSql($viewer);
foreach ($scenarios as $label => $vals) {
    list($l, $c, $g, $r) = $vals;
    $dbh->query("UPDATE userinfo SET looking_for=$l, culture_importance=$c, greek_meaning=$g, relocation_openness=$r WHERE user_id=$candUid");
    $php = MatchScore::compute($viewer, $candUid);
    $sqlR = $dbh->query("SELECT ($sql) AS s FROM userinfo i WHERE i.user_id=$candUid")->fetch_assoc();
    $sqlScore = round((float)$sqlR['s']);
    $status = ($php === $sqlScore) ? 'OK' : "MISMATCH ($php != $sqlScore)";
    printf("  %-30s  %5d  %5d  %s\n", "$label ($l/$c/$g/$r)", $php, $sqlScore, $status);
}

// Restore both
$ovL = (int)($origViewer['looking_for'] ?? 0);
$ovC = (int)($origViewer['culture_importance'] ?? 0);
$ovG = (int)($origViewer['greek_meaning'] ?? 0);
$ovR = (int)($origViewer['relocation_openness'] ?? 0);
$dbh->query("UPDATE userinfo SET looking_for=$ovL, culture_importance=$ovC, greek_meaning=$ovG, relocation_openness=$ovR WHERE user_id=$viewer");

$ocL = (int)($origCand['looking_for'] ?? 0);
$ocC = (int)($origCand['culture_importance'] ?? 0);
$ocG = (int)($origCand['greek_meaning'] ?? 0);
$ocR = (int)($origCand['relocation_openness'] ?? 0);
$dbh->query("UPDATE userinfo SET looking_for=$ocL, culture_importance=$ocC, greek_meaning=$ocG, relocation_openness=$ocR WHERE user_id=$candUid");

echo "\n  (viewer + candidate userinfo restored)\n";
echo "\nDONE\n";
$dbh->close();
