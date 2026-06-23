<?php
// One-shot: insert a token_admin row in `config` so Everett can use the
// /administration/?cmd=login_token bypass without changing Irene's
// admin_password. Chameleon's administration_start.php auto-removes all
// token_admin rows the moment a token is used.
//
// Modes (require token in query string — same one as other _mgs_* scripts):
//   ?token=...                -> status
//   ?token=...&mode=create    -> insert a fresh login token and print the URL
//   ?token=...&mode=cleanup   -> delete any token_admin rows still hanging around
set_time_limit(0); @ini_set('display_errors', 1);
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }
$g = array(); require __DIR__ . '/_include/config/db.php';
$d = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
$d->set_charset('utf8mb4');
header('Content-Type: text/plain');

$mode = $_GET['mode'] ?? 'status';

if ($mode === 'status') {
    echo "current token_admin rows:\n";
    $r = $d->query("SELECT id, module, `option`, LEFT(value, 20) AS val_preview FROM `config` WHERE module='token_admin'");
    $n = 0;
    while ($r && $row = $r->fetch_assoc()) {
        $n++;
        printf("  id=%s option=%s value=%s\n", $row['id'], $row['option'], $row['val_preview']);
    }
    if (!$n) echo "  (none)\n";
    echo "\nUse: ?mode=create  or  ?mode=cleanup\n";
    $d->close(); exit;
}

if ($mode === 'create') {
    // Wipe any prior token_admin rows so we don't accumulate.
    $d->query("DELETE FROM `config` WHERE module='token_admin'");

    $tok = bin2hex(random_bytes(16));
    $stmt = $d->prepare("INSERT INTO `config` (module, `option`, value, type, show_in_admin, position) VALUES ('token_admin', ?, '1', 'text', 0, 0)");
    $stmt->bind_param('s', $tok);
    if (!$stmt->execute()) {
        echo "ERR insert: " . $stmt->error . "\n";
        $d->close(); exit(1);
    }
    echo "INSERTED token_admin row.\n\n";
    echo "Open this URL in your browser (one-shot, gets consumed on use):\n";
    echo "  https://meetgreeksingles.com/administration/index.php?cmd=login_token&token=$tok\n\n";
    echo "After Chameleon accepts it, ALL token_admin rows are auto-deleted by the\n";
    echo "framework (Config::remove('token_admin')) so cleanup is automatic.\n";
    echo "You'll land on the dashboard with an admin session.\n";
    $d->close(); exit;
}

if ($mode === 'cleanup') {
    $r = $d->query("DELETE FROM `config` WHERE module='token_admin'");
    if (!$r) { echo "ERR delete: " . $d->error . "\n"; $d->close(); exit(1); }
    echo "deleted " . $d->affected_rows . " token_admin row(s)\n";
    $d->close(); exit;
}

echo "Unknown mode: " . htmlspecialchars($mode) . "\n";
$d->close();
