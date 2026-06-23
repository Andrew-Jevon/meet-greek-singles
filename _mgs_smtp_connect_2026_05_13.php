<?php
// Test raw TCP connectivity to several SMTP endpoints + ports, to confirm
// the host's outbound block pattern.
set_time_limit(0); @ini_set('display_errors', 1);
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }
header('Content-Type: text/plain');

$targets = array(
    ['tls://smtp.office365.com', 587, 'Office 365 STARTTLS'],
    ['ssl://smtp.office365.com', 465, 'Office 365 implicit SSL'],
    ['smtp.office365.com',       25,  'Office 365 plain 25'],
    ['tls://smtp.gmail.com',     587, 'Gmail STARTTLS (sanity)'],
    ['ssl://smtp.gmail.com',     465, 'Gmail implicit SSL (sanity)'],
    ['localhost',                25,  'Local sendmail / postfix'],
    ['127.0.0.1',                25,  'Local sendmail (IP)'],
);

echo "Outbound SMTP connectivity from prod web server:\n\n";
foreach ($targets as $t) {
    [$host, $port, $label] = $t;
    $ctx = stream_context_create([
        'ssl' => ['verify_peer' => false, 'verify_peer_name' => false],
    ]);
    $start = microtime(true);
    $conn = @stream_socket_client("$host:$port", $errno, $errstr, 5, STREAM_CLIENT_CONNECT, $ctx);
    $elapsed = round((microtime(true) - $start) * 1000);
    if ($conn) {
        $banner = '';
        stream_set_timeout($conn, 2);
        $banner = trim((string) @fgets($conn, 256));
        fclose($conn);
        printf("  [OK]     %-30s %3dms  banner=%s\n", "$host:$port ($label)", $elapsed, substr($banner, 0, 60));
    } else {
        printf("  [FAIL]   %-30s %3dms  errno=%d  err=%s\n", "$host:$port ($label)", $elapsed, $errno, $errstr);
    }
}

echo "\nAlso: PHP mail() (local sendmail via php.ini sendmail_path):\n";
echo "  sendmail_path = " . ini_get('sendmail_path') . "\n";
echo "  mail() exists = " . (function_exists('mail') ? 'yes' : 'no') . "\n";

echo "\nDONE\n";
