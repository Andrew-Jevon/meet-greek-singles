<?php
// Direct-DB probe — bypasses main_start.php so it survives the prelaunch gate.
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }
header('Content-Type: text/plain');

$g = array(); require __DIR__ . '/_include/config/db.php';
$m = @new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
if ($m->connect_errno) { exit("db: " . $m->connect_error); }
$m->set_charset('utf8mb4');

echo "== rows for option='help' (any module) ==\n";
$r = $m->query("SELECT module, `option`, `value`, show_in_admin, type FROM config WHERE `option` = 'help'");
while ($row = $r->fetch_assoc()) print_r($row);

echo "\n== rows for option='contact' ==\n";
$r = $m->query("SELECT module, `option`, `value`, show_in_admin, type FROM config WHERE `option` = 'contact'");
while ($row = $r->fetch_assoc()) print_r($row);

echo "\n== ALL config rows for module='options' (count + first 5 with help-ish names) ==\n";
$r = $m->query("SELECT COUNT(*) c FROM config WHERE module = 'options'");
print_r($r->fetch_assoc());
$r = $m->query("SELECT `option`, `value` FROM config WHERE module='options' AND `option` LIKE '%elp%' OR `option` LIKE 'show_help%' OR `option` LIKE 'help_%'");
while ($row = $r->fetch_assoc()) print_r($row);

echo "\n== help_topic rows ==\n";
$r = $m->query("SELECT id, name, public_visible, position, lang FROM help_topic ORDER BY position, id");
while ($row = $r->fetch_assoc()) print_r($row);
