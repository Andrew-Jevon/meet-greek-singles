<?php
// Test PHP mail() via local Exim relay. Sends to whichever address is in ?to=
// and reports mail()'s return value + any error.
set_time_limit(0); @ini_set('display_errors', 1);
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }
header('Content-Type: text/plain');

$to = $_GET['to'] ?? 'info@meetgreeksingles.com';
if (!filter_var($to, FILTER_VALIDATE_EMAIL)) { echo "Bad ?to=\n"; exit(1); }

$from    = 'info@meetgreeksingles.com';
$subject = 'mail() probe ' . date('Y-m-d H:i:s');
$body    = "Hello,\n\nThis is a test email sent via PHP mail() through the local Exim relay on the GoDaddy host.\n\nSent at " . date('c') . "\n";
$headers = array(
    'From: Meet Greek Singles <' . $from . '>',
    'Reply-To: ' . $from,
    'Return-Path: ' . $from,
    'X-Mailer: PHP/' . phpversion() . ' / mgs probe',
    'MIME-Version: 1.0',
    'Content-Type: text/plain; charset=utf-8',
);

echo "Sending PHP mail()...\n";
echo "  from = $from\n";
echo "  to   = $to\n";
echo "  subject = $subject\n";
echo "\n";

$errors = array();
set_error_handler(function($s,$m) use (&$errors){ $errors[] = $m; return true; });
$result = mail($to, $subject, $body, implode("\r\n", $headers));
restore_error_handler();

echo "mail() returned: " . ($result ? "true (handed off to MTA)" : "FALSE") . "\n";
if ($errors) {
    echo "\nCaptured errors:\n";
    foreach ($errors as $e) echo "  $e\n";
}

echo "\nNote: mail()=true only means the MTA accepted the message for delivery.\n";
echo "      Check the recipient inbox (and spam) to confirm actual delivery.\n";
echo "\nDONE\n";
