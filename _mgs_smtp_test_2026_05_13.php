<?php
// Direct SMTP self-test using Chameleon's Smtp class + the live config row
// in `config` (module='smtp'). Sends one email from info@... to a recipient
// passed in via ?to=... and dumps the full SMTP transcript.
//
// ?token=...&to=<recipient>  -> attempt send
set_time_limit(0); @ini_set('display_errors', 1);
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }
$g = array(); require __DIR__ . '/_include/config/db.php';
$d = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
$d->set_charset('utf8mb4');
header('Content-Type: text/plain');

$to = $_GET['to'] ?? 'info@meetgreeksingles.com';
if (!filter_var($to, FILTER_VALIDATE_EMAIL)) {
    echo "Bad ?to= address\n"; exit(1);
}

// Read SMTP config from `config` table.
$cfg = array();
$stmt = $d->prepare("SELECT `option`, value FROM `config` WHERE module='smtp'");
$stmt->execute();
$rs = $stmt->get_result();
while ($row = $rs->fetch_assoc()) {
    $cfg[$row['option']] = $row['value'];
}

echo "SMTP config:\n";
echo "  server   = " . ($cfg['server'] ?? '(missing)') . "\n";
echo "  port     = " . ($cfg['port'] ?? '(missing)') . "\n";
echo "  user     = " . ($cfg['user'] ?? '(missing)') . "\n";
echo "  password = " . (isset($cfg['password']) ? '(' . strlen($cfg['password']) . ' chars set)' : '(missing)') . "\n";
echo "  active   = " . ($cfg['active'] ?? '(missing)') . "\n";
echo "  sending FROM " . ($cfg['user'] ?? '?') . " TO $to\n\n";

if (!is_readable(__DIR__ . '/_include/current/smtp.class.php')) {
    echo "ERR: smtp.class.php not readable\n"; exit(1);
}
require_once __DIR__ . '/_include/current/smtp.class.php';

// Trap trigger_error to capture auth/send error messages
$errors = array();
set_error_handler(function($severity, $msg, $file, $line) use (&$errors) {
    $errors[] = "trigger_error: $msg";
    return true;
});

$smtp = new Smtp(
    $cfg['server'],
    $cfg['user'],
    $cfg['password'],
    intval($cfg['port'] ?? 587),
    $_SERVER['HTTP_HOST'] ?? 'meetgreeksingles.com'
);
$smtp->setFrom($cfg['user'], 'Meet Greek Singles');
$smtp->setTo($to, '');
$smtp->setSubject('SMTP probe test ' . date('Y-m-d H:i:s'));
$smtp->setMessage('<p>This is a test email from the SMTP probe script.</p><p>Sent at ' . date('c') . '.</p>');

echo "Sending...\n\n";
$result = $smtp->send();
restore_error_handler();

echo "Result: " . ($result ? "TRUE (send() returned true)" : "FALSE (send() returned false)") . "\n";

echo "\nSMTP transcript:\n";
foreach (['connection','helo','STARTTLS','auth','user','password','from','to','data','send','quit'] as $key) {
    $val = $smtp->logGetValue($key);
    if ($val === null) continue;
    // Don't echo back the user-base64 or password-base64 (those are creds)
    if ($key === 'user' || $key === 'password') {
        // Show response code only, not what was sent
        // The log records "command sent" → "response". We logged the b64 string as command and then the response replaces it.
        // Looking at smtp.class.php: log($cmd, $cmd) then $this->log[$key] = $value where value is response.
        // Actually log($cmd, $cmd) sets key=$cmd, value=$cmd. Then sendCmd returns response which is then stored as log[$key] = response.
        // So logGetValue('user') returns the server response to the user b64.
        echo "  $key -> " . substr($val, 0, 80) . (strlen($val) > 80 ? '...' : '') . "\n";
    } else {
        echo "  $key -> " . substr($val, 0, 200) . (strlen($val) > 200 ? '...' : '') . "\n";
    }
}

if (!empty($errors)) {
    echo "\nCaptured trigger_error output:\n";
    foreach ($errors as $e) echo "  $e\n";
}

echo "\nDONE\n";
$d->close();
