<?php
// Greek regions cleanup — replaces geo_state rows for Greece with the
// canonical 13 modern administrative regions (Kallikratis Plan, 2010-).
//
// Why: the stock Chameleon DB shipped a mix of historical prefectures and
// modern regions for Greece, which doesn't match how Greeks today refer to
// their regions and confused the registration flow.  Irene flagged this
// 2026-04-30.
//
// What this script does:
//   1) Discover Greece's country_id from geo_country (matched on iso2='GR')
//   2) Print existing geo_state rows for Greece (audit log before touching)
//   3) Delete existing geo_state rows for Greece
//   4) Insert the canonical 13 admin regions
//   5) Delete geo_city rows that referenced the now-gone state_ids
//      (city is now a free-text user_var, the dropdown is gone — these rows
//       are dead weight)
//   6) Print the new state of geo_state for Greece
//
// Existing user records that referenced the old state_ids: their .state
// column will now be a number with no matching row in geo_state.  Profile
// rendering of state name will fall back to empty / "—".  Acceptable for
// pre-launch — registered test users are a handful.  If we go live with
// existing users, we'd need a state_id remap step (out of scope for this
// pass, no real users yet).
//
// Idempotent (the canonical 13 are inserted with INSERT IGNORE on a deterministic
// state_title ordering, and the script clears prior Greek rows first so re-runs
// converge to the same end state).
//
// Token-protected.  Delete after each use.

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

function q($dbh, $sql) {
    if (!$dbh->query($sql)) {
        echo "  ERR: " . $dbh->error . "\n  SQL: " . substr($sql, 0, 200) . "\n";
        return false;
    }
    return true;
}

echo "Greek regions cleanup\n";
echo "=====================\n\n";

// 1) Greece's country_id (geo_country column is `code`, not `country_code` —
//    confirmed via inspection 2026-05-01)
$cid = null;
$r = $dbh->query("SELECT country_id, country_title, code FROM geo_country WHERE code='GR' OR country_title='Greece' LIMIT 1");
if ($r && $row = $r->fetch_assoc()) {
    $cid = (int) $row['country_id'];
    echo "  Greece: country_id=$cid  title='{$row['country_title']}'  code='{$row['code']}'\n\n";
} else {
    exit("ERR: could not find Greece in geo_country\n");
}

// 2) Audit existing Greek geo_state rows  (column is `code`, not `state_code`)
echo "Existing geo_state rows for Greece (before cleanup):\n";
echo "----------------------------------------------------\n";
$before = array();
$r = $dbh->query("SELECT state_id, state_title, code FROM geo_state WHERE country_id=$cid ORDER BY state_title ASC");
while ($r && $row = $r->fetch_assoc()) {
    $before[] = $row;
    echo "  {$row['state_id']}  {$row['state_title']}  ({$row['code']})\n";
}
echo "  (total: " . count($before) . ")\n\n";

// 3) Delete existing Greek geo_state rows (capture state_ids first so we can
//    sweep geo_city by them in step 5)
$oldStateIds = array_map(function($r){ return (int)$r['state_id']; }, $before);

if (!empty($oldStateIds)) {
    $idList = implode(',', $oldStateIds);
    $cityCount = (int) $dbh->query("SELECT COUNT(*) c FROM geo_city WHERE state_id IN ($idList)")->fetch_assoc()['c'];
    echo "  geo_city rows attached to old Greek states: $cityCount  (will be deleted in step 5)\n";
}

if (q($dbh, "DELETE FROM geo_state WHERE country_id=$cid")) {
    echo "  + cleared " . count($before) . " old geo_state rows\n";
}

// 4) Insert canonical 13 modern admin regions (Kallikratis Plan, 2010-).
//    Ordered alphabetically by their canonical English name so admin and
//    dropdown rendering is predictable.  state_code follows the ISO 3166-2:GR
//    prefixes where possible.
$regions = array(
    array('Attica',                      'GR-A'),
    array('Central Greece',              'GR-H'),
    array('Central Macedonia',           'GR-B'),
    array('Crete',                       'GR-M'),
    array('Eastern Macedonia and Thrace','GR-A1'),
    array('Epirus',                      'GR-D'),
    array('Ionian Islands',              'GR-F'),
    array('North Aegean',                'GR-K'),
    array('Peloponnese',                 'GR-J'),
    array('South Aegean',                'GR-L'),
    array('Thessaly',                    'GR-E'),
    array('Western Greece',              'GR-G'),
    array('Western Macedonia',           'GR-C'),
);

echo "\nInserting canonical 13 modern Greek administrative regions:\n";
echo "-----------------------------------------------------------\n";
$inserted = 0;
foreach ($regions as $reg) {
    $title = $dbh->real_escape_string($reg[0]);
    $code  = $dbh->real_escape_string($reg[1]);
    if (q($dbh, "INSERT INTO geo_state (country_id, state_title, code) VALUES ($cid, '$title', '$code')")) {
        echo "  + $title  ($code)  state_id=" . $dbh->insert_id . "\n";
        $inserted++;
    }
}
echo "  (inserted: $inserted of " . count($regions) . ")\n\n";

// 5) Sweep geo_city for the old (deleted) Greek states.  City is a free-text
//    user_var now, so the geo_city rows for Greece are dead weight.
if (!empty($oldStateIds)) {
    $idList = implode(',', $oldStateIds);
    $r = $dbh->query("SELECT COUNT(*) c FROM geo_city WHERE state_id IN ($idList)");
    $n = (int) $r->fetch_assoc()['c'];
    if ($n > 0) {
        if (q($dbh, "DELETE FROM geo_city WHERE state_id IN ($idList)")) {
            echo "  + cleared $n orphaned geo_city rows for Greece\n\n";
        }
    } else {
        echo "  = no geo_city rows attached to old Greek states\n\n";
    }
}

// 6) Print the new state of Greek geo_state
echo "Greek geo_state rows after cleanup:\n";
echo "-----------------------------------\n";
$r = $dbh->query("SELECT state_id, state_title, code FROM geo_state WHERE country_id=$cid ORDER BY state_title ASC");
$count = 0;
while ($r && $row = $r->fetch_assoc()) {
    echo "  {$row['state_id']}  {$row['state_title']}  ({$row['code']})\n";
    $count++;
}
echo "  (total: $count)\n\n";

echo "DONE\n";
$dbh->close();
