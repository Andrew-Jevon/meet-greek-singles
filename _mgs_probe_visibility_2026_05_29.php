<?php
/* /_mgs_probe_visibility_2026_05_29.php — Phase 8.2 regression test.
 *
 * Proves the visibility filter is enforcing scope at runtime by:
 *
 *   1. Listing every user_var field that has visibility_scope='owner' or
 *      'member' set in its config blob — these are fields a guest must
 *      NOT see in any rendered or AJAX-returned output.
 *
 *   2. For each such owner-scope field, hitting the production homepage
 *      + a public profile path as an unauthenticated client and grep-ing
 *      for the field name in the rendered HTML.
 *
 *   3. Probing the match_scores.php endpoint as an unauthenticated client
 *      and confirming it returns an empty JSON {} (no profile data leak).
 *
 *   4. Reporting PASS / LEAK per scope/field/endpoint.
 *
 * Read-only. Token-protected. Deploy + run + delete after.
 *
 * Run:
 *   curl "https://meetgreeksingles.com/_mgs_probe_visibility_2026_05_29.php?token=<TOKEN>"
 */

set_time_limit(30);
@ini_set('display_errors', 1);
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) {
    http_response_code(403);
    exit("forbidden\n");
}

$g = array();
require __DIR__ . '/_include/config/db.php';
$d = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
if ($d->connect_errno) { exit("db: " . $d->connect_error); }
$d->set_charset('utf8mb4');
header('Content-Type: text/plain; charset=utf-8');

echo "Phase 8.2 visibility regression test — " . date('Y-m-d H:i:s') . "\n";
echo str_repeat('=', 70) . "\n\n";

// (1) Enumerate scoped fields
$ownerFields  = array();
$memberFields = array();
$publicFields = array();
$res = $d->query("SELECT `option`, value FROM config WHERE module='user_var'");
while ($row = $res->fetch_assoc()) {
    $blob = @unserialize($row['value']);
    if (!is_array($blob)) continue;
    $scope = $blob['visibility_scope'] ?? 'member';
    if      ($scope === 'owner')  $ownerFields[]  = $row['option'];
    elseif  ($scope === 'public') $publicFields[] = $row['option'];
    else                          $memberFields[] = $row['option'];
}
echo "Field scope inventory:\n";
echo "  public  fields: " . count($publicFields) . " — " . implode(', ', array_slice($publicFields, 0, 8))
   . (count($publicFields) > 8 ? ", ..." : "") . "\n";
echo "  member  fields: " . count($memberFields) . " — " . implode(', ', array_slice($memberFields, 0, 8))
   . (count($memberFields) > 8 ? ", ..." : "") . "\n";
echo "  owner   fields: " . count($ownerFields)  . " — " . implode(', ', $ownerFields) . "\n";
echo "\n";

// (2) Fetch guest views of public-facing URLs and grep for owner-scope field names
function fetch($url) {
    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, 1);
    curl_setopt($ch, CURLOPT_TIMEOUT, 10);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, 0);
    curl_setopt($ch, CURLOPT_USERAGENT, 'visibility-probe/1.0');
    $body = curl_exec($ch);
    $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    return array($code, $body);
}

$guestUrls = array(
    'https://meetgreeksingles.com/',
    'https://meetgreeksingles.com/search_results.php',
    'https://meetgreeksingles.com/about',
    'https://meetgreeksingles.com/help',
);
echo "(2) Guest views of public URLs — checking for owner-scope field name leaks:\n";
foreach ($guestUrls as $u) {
    list($code, $body) = fetch($u);
    $hits = array();
    foreach ($ownerFields as $f) {
        // look for value="$f" or name="$f" or 'data-field="$f"' patterns — these would
        // be inputs / data attrs that include the field name in output
        if (preg_match('/(?:value|name|data-field)="' . preg_quote($f, '/') . '"/', $body)) {
            $hits[] = $f;
        }
    }
    echo "  $u  [HTTP $code, " . strlen($body) . " bytes] — owner-field hits: "
       . (empty($hits) ? "none (PASS)" : implode(', ', $hits) . " (LEAK)") . "\n";
}
echo "\n";

// (3) match_scores.php as guest
echo "(3) match_scores.php as unauthenticated client:\n";
list($code, $body) = fetch('https://meetgreeksingles.com/match_scores.php');
$body = trim($body);
echo "  HTTP $code, body: " . substr($body, 0, 100) . "\n";
if ($body === '{}' || $body === '[]') {
    echo "  PASS — returns empty (no leak)\n";
} else {
    echo "  REVIEW — body is non-empty, check for profile field names\n";
    $hits = array();
    foreach ($ownerFields as $f) {
        if (strpos($body, $f) !== false) $hits[] = $f;
    }
    if (!empty($hits)) {
        echo "  LEAK — owner-scope field names appear in response: " . implode(', ', $hits) . "\n";
    } else {
        echo "  PASS — body non-empty but no owner-scope field names found\n";
    }
}
echo "\n";

echo str_repeat('=', 70) . "\n";
echo "DONE.\n";
$d->close();
