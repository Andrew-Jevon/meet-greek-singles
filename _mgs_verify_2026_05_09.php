<?php
/* 2026-05-09 verification probe — confirm the EmailVerification gate is
 * loaded and the install script's effects are live. Token-protected. Delete
 * after run. */
@ini_set('display_errors', 1);
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }

header('Content-Type: text/plain');

// 1. Check the class file is on disk and loadable
$path = __DIR__ . '/_include/current/email_verification.class.php';
echo "1. EmailVerification class file\n";
echo "   path=$path\n";
echo "   exists: " . (is_readable($path) ? "YES" : "NO") . "\n";
if (is_readable($path)) {
    require_once $path;
    echo "   class_exists('EmailVerification'): " . (class_exists('EmailVerification') ? "YES" : "NO") . "\n";
    echo "   has apply() method: " . (method_exists('EmailVerification', 'apply') ? "YES" : "NO") . "\n";
}

// 2. Check common.class.php contains the hook
echo "\n2. common.class.php hook\n";
$common = file_get_contents(__DIR__ . '/_include/current/common.class.php');
$hookPresent = (strpos($common, 'EmailVerification::apply()') !== false);
echo "   contains 'EmailVerification::apply()': " . ($hookPresent ? "YES" : "NO") . "\n";

// 3. Verify install effects on DB
$g = array();
require __DIR__ . '/_include/config/db.php';
$d = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
$d->set_charset('utf8mb4');

echo "\n3. user_var question_title state (after install)\n";
foreach (['hair', 'status', 'i_am_here_to', 'weight', 'orign', 'height'] as $name) {
    $r = $d->query("SELECT value FROM config WHERE module='user_var' AND `option`='" . $d->real_escape_string($name) . "'");
    $row = $r ? $r->fetch_assoc() : null;
    if (!$row) { echo "   $name: not found\n"; continue; }
    $v = @unserialize($row['value']);
    if (!is_array($v)) { echo "   $name: unserialize failed\n"; continue; }
    $qt = $v['question_title'] ?? '(missing)';
    $ans = $v['answer'] ?? '(missing)';
    $type = $v['type'] ?? '(missing)';
    $title = $v['title'] ?? '(missing)';
    echo "   $name: type=$type title='$title' question_title='" . substr($qt, 0, 30) . "' answer='" . substr($ans, 0, 30) . "'\n";
}

echo "\n4. active_code state\n";
$r = $d->query("SELECT COUNT(*) c FROM user WHERE active_code != ''");
echo "   users with active_code (unconfirmed): " . $r->fetch_assoc()['c'] . "\n";
$r = $d->query("SELECT COUNT(*) c FROM user");
echo "   total users: " . $r->fetch_assoc()['c'] . "\n";

echo "\nDONE\n";
$d->close();
