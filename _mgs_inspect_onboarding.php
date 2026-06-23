<?php
@ini_set('display_errors', 1);
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }
$g = array(); require __DIR__ . '/_include/config/db.php';
$d = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
header('Content-Type: text/plain');
echo "All user_var rows with is_onboarding=1:\n";
echo "========================================\n\n";
$r = $d->query("SELECT `option`, position, value FROM config WHERE module='user_var' ORDER BY position ASC");
while ($r && $row = $r->fetch_assoc()) {
    $v = @unserialize($row['value']);
    if (!is_array($v)) continue;
    $isObd = !empty($v['is_onboarding']) ? 'YES' : ' no';
    $title = $v['title'] ?? '(no title)';
    $type  = $v['type']  ?? '?';
    $sub   = $v['subtitle'] ?? '';
    if ($isObd === 'YES') {
        echo "  pos={$row['position']}  option={$row['option']}  type=$type\n";
        echo "    title:    '$title'\n";
        echo "    subtitle: '$sub'\n";
        echo "\n";
    }
}
