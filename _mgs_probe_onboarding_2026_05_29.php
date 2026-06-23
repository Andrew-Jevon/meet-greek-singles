<?php
/* /_mgs_probe_onboarding_2026_05_29.php — corrected onboarding option probe.
 *
 * Replaces the 2026-05-28 probe which incorrectly queried a non-existent
 * `user_var` table. Production stores user_var metadata as serialized PHP
 * blobs in the `config` table where module='user_var'. This probe reads
 * the blob, unserialize()s it, and reports the title + answer options for
 * each of the 4 onboarding fields.
 *
 * Read-only, token-protected. Deploy + run + delete after.
 *
 * Run:
 *   curl "https://meetgreeksingles.com/_mgs_probe_onboarding_2026_05_29.php?token=<TOKEN>"
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

echo "Onboarding option text probe — " . date('Y-m-d H:i:s') . "\n";
echo str_repeat('=', 70) . "\n\n";

$fields = array('looking_for', 'culture_importance', 'greek_meaning', 'relocation_openness');

foreach ($fields as $name) {
    echo "Field: $name\n";
    $stmt = $d->prepare("SELECT `option`, value FROM config WHERE module='user_var' AND `option` = ?");
    $stmt->bind_param('s', $name);
    $stmt->execute();
    $r = $stmt->get_result();
    $row = $r->fetch_assoc();
    if (!$row) {
        echo "  NOT FOUND in config table.\n\n";
        continue;
    }
    $blob = @unserialize($row['value']);
    if (!is_array($blob)) {
        echo "  Could not unserialize blob. Raw first 200 chars:\n";
        echo "    " . substr($row['value'], 0, 200) . "\n\n";
        continue;
    }
    echo "  title:        " . ($blob['title']        ?? '(unset)') . "\n";
    echo "  type:         " . ($blob['type']         ?? '(unset)') . "\n";
    echo "  position:     " . ($blob['position']     ?? '(unset)') . "\n";
    echo "  is_onboarding:" . ($blob['is_onboarding']?? '(unset)') . "\n";
    echo "  is_searchable:" . ($blob['is_searchable']?? '(unset)') . "\n";
    echo "  visibility:   " . ($blob['visibility_scope'] ?? '(unset)') . "\n";
    if (isset($blob['title_options']) && is_array($blob['title_options'])) {
        echo "  options:\n";
        $i = 1;
        foreach ($blob['title_options'] as $k => $v) {
            echo "    [$i] $k -> $v\n";
            $i++;
        }
    } else {
        echo "  options:      (no title_options array found)\n";
    }
    echo "\n";
    $stmt->close();
}

echo str_repeat('=', 70) . "\n";
echo "DONE. Compare title + options against firstC.md §4.2 spec.\n";
$d->close();
