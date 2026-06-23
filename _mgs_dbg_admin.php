<?php
// Token-protected probe to debug visibility_scope gating.
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }

header('Content-Type: text/plain');
echo "SERVER context\n--------------\n";
echo "SCRIPT_NAME       = " . ($_SERVER['SCRIPT_NAME'] ?? 'unset') . "\n";
echo "PHP_SELF          = " . ($_SERVER['PHP_SELF'] ?? 'unset') . "\n";
echo "REQUEST_URI       = " . ($_SERVER['REQUEST_URI'] ?? 'unset') . "\n";
echo "DOCUMENT_ROOT     = " . ($_SERVER['DOCUMENT_ROOT'] ?? 'unset') . "\n";
echo "SCRIPT_FILENAME   = " . ($_SERVER['SCRIPT_FILENAME'] ?? 'unset') . "\n";
echo "\n";
echo "Path-based isAdminArea() check:\n";
echo "  strpos(SCRIPT_NAME, '/administration/') !== false  =>  ";
$found = strpos($_SERVER['SCRIPT_NAME'] ?? '', '/administration/');
var_dump($found);
echo "\n";

// Re-check the deployed prelaunch.class.php
$prelaunch = @file_get_contents(__DIR__ . '/_include/current/prelaunch.class.php');
$onboarding = @file_get_contents(__DIR__ . '/_include/current/onboarding.class.php');
echo "deployed prelaunch.class.php has new isAdminArea: ";
var_dump(strpos($prelaunch, "Path check first \u{2014} catches any file") !== false);
echo "deployed onboarding.class.php has admin path check: ";
var_dump(strpos($onboarding, "Path check first because") !== false);
