<?php
/* /_mgs_probe_onboarding_options_2026_05_28.php
 *
 * Phase 5 verification probe (firstC.md §4.2). Read-only.
 *
 * Dumps the current user_var rows for the 4 onboarding fields:
 *   looking_for, culture_importance, greek_meaning, relocation_openness
 *
 * Then diffs the stored option text against firstC.md §4.2's verbatim
 * spec and prints "PASS" or "DRIFT" per field.
 *
 * No DB writes. No data export beyond the option text already visible
 * in the UI. Token-protected per project convention.
 *
 * Run pattern (per 5.11_prompt.md):
 *   curl "https://meetgreeksingles.com/_mgs_probe_onboarding_options_2026_05_28.php?token=<TOKEN>"
 *
 * Delete from prod after running.
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

echo "Onboarding options vs firstC.md \xC2\xA74.2 — " . date('Y-m-d H:i:s') . "\n";
echo str_repeat('=', 70) . "\n\n";

/* firstC.md §4.2 spec — exact option text, exact order. */
$spec = array(
    'looking_for' => array(
        'title' => 'What are you looking for?',
        'options' => array(
            'A meaningful, long-term relationship',
            'Marriage',
            'A life partner',
            "Something serious, but let\xE2\x80\x99s see where it leads",
            'Friendship first',
        ),
    ),
    'culture_importance' => array(
        'title' => 'How important is Greek culture in your life?',
        'options' => array(
            "It\xE2\x80\x99s a core part of who I am",
            'Very important',
            'Somewhat important',
            'Not very important, but I appreciate it',
            'Not important',
        ),
    ),
    'greek_meaning' => array(
        'title' => 'What does being Greek mean to you?',
        'options' => array(
            'Family and traditions',
            'Language and communication',
            'Faith and values',
            'Cultural lifestyle (food, music, celebrations)',
            'Connection to Greece',
            "It\xE2\x80\x99s part of my identity, but I define it in my own way",
        ),
    ),
    'relocation_openness' => array(
        'title' => 'Do you see yourself open to relocating for the right person?',
        'options' => array(
            "Yes \xE2\x80\x94 I\xE2\x80\x99m open to relocating anywhere",
            "Yes \xE2\x80\x94 but preferably within Greece",
            "Yes \xE2\x80\x94 but preferably abroad (e.g., Europe, USA, Australia)",
            "Maybe \xE2\x80\x94 it depends on the connection",
            "No \xE2\x80\x94 I prefer to stay where I am",
        ),
    ),
);

/* Try the most plausible column names. Chameleon's user_var schema typically
 * has: id, name, question_title, answer, type, group, ...; the 'answer' column
 * holds the serialized option array. */
$probeCols = "name, question_title, answer, type";
$names = "'looking_for','culture_importance','greek_meaning','relocation_openness'";

$res = $d->query("SELECT $probeCols FROM user_var WHERE name IN ($names) ORDER BY FIELD(name,$names)");
if (!$res) {
    echo "ERR: " . $d->error . "\n";
    exit(1);
}

$found = array();
while ($row = $res->fetch_assoc()) {
    $found[$row['name']] = $row;
}

$verdict = array();
foreach (array_keys($spec) as $fname) {
    echo "Field: $fname\n";
    if (!isset($found[$fname])) {
        echo "  MISSING in DB.\n\n";
        $verdict[$fname] = 'MISSING';
        continue;
    }
    $row = $found[$fname];
    echo "  type           = " . $row['type'] . "\n";
    echo "  question_title = " . ($row['question_title'] === '' ? '(empty)' : $row['question_title']) . "\n";

    /* Chameleon serializes via PHP serialize() — try that first.
     * Fallback to JSON if it's actually json-encoded. */
    $opts = @unserialize($row['answer']);
    if ($opts === false || !is_array($opts)) {
        $opts = json_decode($row['answer'], true);
    }
    if (!is_array($opts)) {
        echo "  answer is not parseable as serialize/json. Raw (first 240 chars):\n";
        echo "    " . substr($row['answer'], 0, 240) . "\n\n";
        $verdict[$fname] = 'UNPARSEABLE';
        continue;
    }

    /* Some Chameleon schemas store options as id => text, others as numeric
     * arrays. Flatten to a values-only list for compare. */
    $actual = array_values(array_map(function ($v) {
        if (is_array($v) && isset($v['title'])) return $v['title'];
        return (string) $v;
    }, $opts));

    $expected = $spec[$fname]['options'];

    if ($actual === $expected) {
        echo "  options: PASS (" . count($actual) . " options, exact match)\n";
        $verdict[$fname] = 'PASS';
    } else {
        echo "  options: DRIFT\n";
        $max = max(count($actual), count($expected));
        for ($i = 0; $i < $max; $i++) {
            $a = isset($actual[$i])   ? $actual[$i]   : '(missing)';
            $e = isset($expected[$i]) ? $expected[$i] : '(unexpected)';
            $marker = ($a === $e) ? '  ' : '!=';
            echo "    [$i] $marker  spec: $e\n";
            echo "          " . str_repeat(' ', 2) . "db:   $a\n";
        }
        $verdict[$fname] = 'DRIFT';
    }
    echo "\n";
}

echo str_repeat('=', 70) . "\n";
echo "SUMMARY:\n";
foreach ($verdict as $f => $v) {
    echo "  $f: $v\n";
}
echo "\n";
$d->close();
