<?php
/* /match_scores.php — small JSON endpoint that returns compatibility scores
 * for a list of candidate user_ids, computed against the currently logged-in
 * viewer using MatchScore. Called by the badge JS in
 * _list_users_info.html on the search results page.
 *
 * Why a standalone script and not a hook into ajax.php:
 *   ajax.php is a long switchboard of named actions in encoded core; adding
 *   a new action requires modifying it. A standalone script keeps the
 *   match-score concern self-contained, can be removed in one DELETE if we
 *   ever revisit the approach, and bypasses Chameleon's bootstrap (so we
 *   don't trigger the prelaunch / onboarding gates from a per-card AJAX
 *   call that's just reading data).
 *
 * Privacy invariant (Phase 8.2):
 *   This endpoint returns ONLY scalar compatibility scores (0-100),
 *   NEVER user profile fields. That property keeps it outside the
 *   visibility-filter scope. If a future change makes this endpoint
 *   emit any user profile field, that field MUST be filtered through
 *   Visibility::filterUserRow($row, $viewerUid, $ownerUid) before
 *   json_encode. See the architecture comment block at the top of
 *   _include/current/visibility_filter.class.php.
 *
 * Session sharing:
 *   Chameleon stores user_id in the standard PHP session ($_SESSION['user_id']).
 *   session_start() here picks up the same `sid` cookie the main site sets
 *   after login, so we know who's asking without re-authenticating.
 *
 * Returns:
 *   { "<uid>": <0-100>, "<uid>": <0-100>, ... }   on success
 *   {}                                             if not logged in / no answers
 */

set_time_limit(10);
@ini_set('display_errors', 0);   // never leak error HTML in JSON response

// Chameleon uses 'sid' as the session name (per securimage.class.php:422 +
// the rest of the bootstrap). We must set the same name before session_start
// or PHP creates a brand-new session keyed off PHPSESSID and our cookie is
// ignored.
session_name('sid');
session_start();

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');

// Chameleon prefixes session keys with `.<host>_` to keep shared-hosting
// installs from colliding (so `user_id` is actually `.meetgreeksingles.com_user_id`).
// Mirror that key construction so we read the same value Chameleon's
// get_session('user_id') would return.
$sessKey = '.' . ($_SERVER['HTTP_HOST'] ?? '') . '_user_id';
$viewerUid = isset($_SESSION[$sessKey]) ? (int) $_SESSION[$sessKey] : 0;
// Fall-back: bare 'user_id' for any environment that doesn't use the prefix.
if ($viewerUid <= 0 && isset($_SESSION['user_id'])) {
    $viewerUid = (int) $_SESSION['user_id'];
}

if ($viewerUid <= 0) { echo '{}'; exit; }

// Validate uids array — accept up to 50 candidates per call. Anything more
// would mean an unusually large search page; cap to keep DB load bounded.
$uids = isset($_POST['uids']) ? (array) $_POST['uids'] : array();
if (count($uids) > 50) $uids = array_slice($uids, 0, 50);
$cleanUids = array();
foreach ($uids as $u) {
    $u = (int) $u;
    if ($u > 0 && $u !== $viewerUid) $cleanUids[$u] = true;
}
if (!$cleanUids) { echo '{}'; exit; }

// Bootstrap DB only (skip Chameleon's heavy main_start.php — we just need
// userinfo reads, not the request-scoped hooks).
$g = array();
require __DIR__ . '/_include/config/db.php';
$dbh = @new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
if ($dbh->connect_errno) { echo '{}'; exit; }
$dbh->set_charset('utf8mb4');

// Lightweight DB shim — MatchScore depends on a class named DB with a
// row($sql) static method. Chameleon's full DB class needs main_start.php.
// We provide just the row() method MatchScore actually uses.
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

if (!MatchScore::userHasAnswers($viewerUid)) { echo '{}'; exit; }

$out = array();
foreach (array_keys($cleanUids) as $uid) {
    $score = MatchScore::compute($viewerUid, $uid);
    if ($score > 0) $out[(string) $uid] = $score;
}

echo json_encode($out);
$dbh->close();
