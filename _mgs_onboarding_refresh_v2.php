<?php
/* 2026-05-04 v2 onboarding refresh per Irene:
 *   - Deactivates the stray greek_values_traditions field (is_onboarding=0,
 *     status=inactive) — leftover from an earlier iteration that wasn't
 *     caught by the M3-fields demote.
 *   - Adds subtitle copy under each of the four new onboarding fields.
 * Idempotent. Token-protected.
 */

set_time_limit(0);
@ini_set('display_errors', 1);
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }

$g = array();
require __DIR__ . '/_include/config/db.php';
$d = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
if ($d->connect_errno) exit("db: " . $d->connect_error);
$d->set_charset('utf8mb4');
header('Content-Type: text/plain');

function mutate(&$d, $name, $changes) {
    $r = $d->query("SELECT value FROM config WHERE module='user_var' AND `option`='$name'");
    $row = $r ? $r->fetch_assoc() : null;
    if (!$row) { echo "  = $name not found\n"; return; }
    $v = @unserialize($row['value']);
    if (!is_array($v)) { echo "  ! $name unserialize failed\n"; return; }
    foreach ($changes as $k => $val) $v[$k] = $val;
    $safe = $d->real_escape_string(serialize($v));
    if ($d->query("UPDATE config SET value='$safe' WHERE module='user_var' AND `option`='$name'")) {
        $applied = array();
        foreach ($changes as $k => $val) $applied[] = "$k=" . (is_string($val) ? "'$val'" : $val);
        echo "  ~ $name  → " . implode(', ', $applied) . "\n";
    }
}

echo "Onboarding refresh v2\n";
echo "=====================\n\n";

// 1. Demote the stray greek_values_traditions (was the unwanted 5th card)
mutate($d, 'greek_values_traditions', array(
    'is_onboarding' => 0,
    'status'        => 'inactive',
));

// 2. Add Irene's subtitles to the 4 active onboarding fields
$subtitles = array(
    'looking_for'         => "Let's begin with what matters most to you.",
    'culture_importance'  => "Your connection to Greece is part of your story.",
    'greek_meaning'       => "The strongest connections are built on shared values.",
    'relocation_openness' => "Life can take us anywhere — what feels right to you?",
);
foreach ($subtitles as $name => $sub) {
    mutate($d, $name, array('subtitle' => $sub));
}

echo "\nDONE\n";
$d->close();
