<?php
/* 2026-05-09 install — two changes per Irene:
 *
 *   A) Clear `question_title` (and the related `answer` JSON) from the six
 *      user_var entries that drive Chameleon's `/join2` yes/no card-flip
 *      questions. Once cleared, Chameleon's encoded core has no items to
 *      render in step 1 and the user moves directly to step 3 ("Kickstart
 *      your profile" — about_me / interested_in / captcha). No more
 *      duplicate questions before our /onboarding.php cards.
 *
 *      Six entries today: hair, status, i_am_here_to, weight, orign,
 *      height. We only clear `question_title` + `answer` — type/title/etc.
 *      remain so the field continues to function as a regular profile
 *      field elsewhere (admin, profile editor, etc.).
 *
 *   B) Clear `active_code` on the 18 existing unconfirmed users so the new
 *      EmailVerification gate (deployed alongside this script) doesn't
 *      retroactively lock out Irene's test accounts. Going forward, every
 *      newly-registered user keeps their `active_code` until they click
 *      the link, and the gate bounces them to /email_not_confirmed.php
 *      until then.
 *
 * Token-protected. Idempotent. Delete after each run.
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

echo "Install 2026-05-09\n";
echo "==================\n\n";

// ── A. Clear question_title + answer on user_var entries ─────────────────
echo "A. Clear question_title + answer on user_var entries\n";
echo "----------------------------------------------------\n";
$names = ['hair', 'status', 'i_am_here_to', 'weight', 'orign', 'height'];
foreach ($names as $name) {
    $r = $d->query("SELECT value FROM config WHERE module='user_var' AND `option`='" . $d->real_escape_string($name) . "'");
    $row = $r ? $r->fetch_assoc() : null;
    if (!$row) { echo "  = $name not found, skipping\n"; continue; }
    $v = @unserialize($row['value']);
    if (!is_array($v)) { echo "  ! $name unserialize failed\n"; continue; }

    $hadQT = !empty($v['question_title']);
    $hadAns = isset($v['answer']);
    if (isset($v['question_title'])) $v['question_title'] = '';
    if (isset($v['answer']))         $v['answer']         = '';
    if (isset($v['chart']))          $v['chart']          = '0';

    $safe = $d->real_escape_string(serialize($v));
    if ($d->query("UPDATE config SET value='$safe' WHERE module='user_var' AND `option`='" . $d->real_escape_string($name) . "'")) {
        echo "  ~ $name  → cleared question_title=" . ($hadQT?'YES':'no') . " answer=" . ($hadAns?'YES':'no') . " chart=0\n";
    } else {
        echo "  ! $name update failed: " . $d->error . "\n";
    }
}

// ── B. Clear active_code on existing unconfirmed test users ──────────────
echo "\nB. Clear active_code on existing unconfirmed users\n";
echo "--------------------------------------------------\n";
$r = $d->query("SELECT COUNT(*) c FROM user WHERE active_code != ''");
$before = (int) $r->fetch_assoc()['c'];
echo "  before: $before unconfirmed\n";

if ($d->query("UPDATE user SET active_code = '' WHERE active_code != ''")) {
    $cleared = $d->affected_rows;
    echo "  + cleared active_code on $cleared user rows\n";
} else {
    echo "  ! update failed: " . $d->error . "\n";
}

$r = $d->query("SELECT COUNT(*) c FROM user WHERE active_code != ''");
$after = (int) $r->fetch_assoc()['c'];
echo "  after: $after unconfirmed\n";

echo "\nDONE\n";
$d->close();
