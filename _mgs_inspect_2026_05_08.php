<?php
// Inspection probe — find:
//   1) user_var entries with question_title set (drive /join2 yes/no cards)
//   2) admin options related to email verification (drive email gating)
@ini_set('display_errors', 1);
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }

$g = array();
require __DIR__ . '/_include/config/db.php';
$d = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
if ($d->connect_errno) exit("db: " . $d->connect_error);
$d->set_charset('utf8mb4');
header('Content-Type: text/plain');

echo "== 1. user_var entries with question_title set ==\n";
$r = $d->query("SELECT `option`, position, value FROM config WHERE module='user_var' ORDER BY position ASC");
while ($r && $row = $r->fetch_assoc()) {
    $v = @unserialize($row['value']);
    if (!is_array($v)) continue;
    if (empty($v['question_title'])) continue;
    echo "  pos={$row['position']}  option={$row['option']}\n";
    echo "    type={$v['type']}\n";
    echo "    title='{$v['title']}'\n";
    echo "    question_title='{$v['question_title']}'\n";
    echo "    chart=" . ($v['chart'] ?? '(none)') . "\n";
    echo "    has_answer_field=" . (isset($v['answer']) ? 'YES' : 'no') . "\n";
    echo "\n";
}

echo "\n== 2. admin options matching keywords email/confirm/verify ==\n";
$r = $d->query("SELECT `option`, value FROM config
                  WHERE module IN ('options','template_options')
                    AND (LOWER(`option`) LIKE '%email%' OR LOWER(`option`) LIKE '%confirm%' OR LOWER(`option`) LIKE '%verif%' OR LOWER(`option`) LIKE '%active%')
                  ORDER BY module, `option` ASC");
while ($r && $row = $r->fetch_assoc()) {
    $val = $row['value'];
    if (strlen($val) > 80) $val = substr($val, 0, 80) . '...';
    echo "  {$row['option']} = $val\n";
}

echo "\n== 3. mail-related options too ==\n";
$r = $d->query("SELECT `option`, value FROM config
                  WHERE module IN ('options','template_options')
                    AND (LOWER(`option`) LIKE '%mail%' OR LOWER(`option`) LIKE '%register%' OR LOWER(`option`) LIKE '%join%')
                  ORDER BY module, `option` ASC LIMIT 40");
while ($r && $row = $r->fetch_assoc()) {
    $val = $row['value'];
    if (strlen($val) > 80) $val = substr($val, 0, 80) . '...';
    echo "  {$row['option']} = $val\n";
}

echo "\nDONE\n";
$d->close();
