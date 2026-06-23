<?php
// Trace help.php behaviour. Bypass the prelaunch gate by including main_start
// then echoing each step before the redirect chain happens.
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }

// Capture any header() calls so toHomePage() doesn't actually redirect us.
ob_start();
$captured = [];
header_remove();

$area = "public";
include("./_include/core/main_start.php");

ob_end_clean();
header_remove();
header('Content-Type: text/plain');

echo "after main_start.\n";
echo "isOptionActive('help')   = " . var_export(Common::isOptionActive('help'), true) . "\n";
echo "isOptionActive('contact')= " . var_export(Common::isOptionActive('contact'), true) . "\n";
global $g;
echo "g[options][help]         = " . var_export($g['options']['help'] ?? '(null)', true) . "\n";
echo "g[options][contact]      = " . var_export($g['options']['contact'] ?? '(null)', true) . "\n";
echo "Prelaunch::currentMode() = " . Prelaunch::currentMode() . "\n";
echo "guid()                   = " . var_export(guid(), true) . "\n";
echo "SCRIPT_NAME              = " . ($_SERVER['SCRIPT_NAME'] ?? '?') . "\n";
echo "global \$p                = " . var_export($GLOBALS['p'] ?? null, true) . "\n";
