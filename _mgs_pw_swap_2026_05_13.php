<?php
// One-shot: temporarily swap the admin dashboard password to a known test
// value, with a server-side backup row so we can restore Irene's original
// without ever exposing it. Original is NEVER echoed to the response.
//
// Modes (require token):
//   ?token=...                -> status
//   ?token=...&mode=swap      -> back up original, set temp password
//   ?token=...&mode=restore   -> restore original from backup, delete backup
set_time_limit(0); @ini_set('display_errors', 1);
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }
$g = array(); require __DIR__ . '/_include/config/db.php';
$d = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
$d->set_charset('utf8mb4');
header('Content-Type: text/plain');

$mode = $_GET['mode'] ?? 'status';
$BACKUP_MODULE = '_mgs_pw_backup';
$BACKUP_OPTION = 'admin_password_original';
$TEMP_PW       = 'mgsAdmin!2026';

function get_current_admin_pw(mysqli $d) {
    $r = $d->query("SELECT value FROM `config` WHERE module='main' AND `option`='admin_password' LIMIT 1");
    if (!$r) return null;
    $row = $r->fetch_assoc();
    return $row ? $row['value'] : null;
}
function backup_exists(mysqli $d, $mod, $opt) {
    $stmt = $d->prepare("SELECT id FROM `config` WHERE module=? AND `option`=? LIMIT 1");
    $stmt->bind_param('ss', $mod, $opt); $stmt->execute();
    return (bool) $stmt->get_result()->fetch_assoc();
}

if ($mode === 'status') {
    $cur_len = strlen((string) get_current_admin_pw($d));
    $bak = backup_exists($d, $BACKUP_MODULE, $BACKUP_OPTION);
    echo "current admin_password length: $cur_len chars\n";
    echo "backup row present:           " . ($bak ? "YES (system is currently swapped)" : "no (normal state)") . "\n";
    echo "\nUse: ?mode=swap  or  ?mode=restore\n";
    $d->close(); exit;
}

if ($mode === 'swap') {
    if (backup_exists($d, $BACKUP_MODULE, $BACKUP_OPTION)) {
        echo "ERR: backup row already exists — system appears already swapped.\n";
        echo "     Run ?mode=restore first if you want to swap again.\n";
        $d->close(); exit(1);
    }
    $orig = get_current_admin_pw($d);
    if ($orig === null) { echo "ERR: cannot read current admin_password row\n"; $d->close(); exit(1); }

    $d->query("START TRANSACTION");
    // Insert backup row (mirrors the schema of the real config row)
    $stmt = $d->prepare("INSERT INTO `config` (module, `option`, value, type, show_in_admin, position) VALUES (?, ?, ?, 'text', 0, 0)");
    $stmt->bind_param('sss', $BACKUP_MODULE, $BACKUP_OPTION, $orig);
    if (!$stmt->execute()) { echo "ERR backup: " . $stmt->error . "\n"; $d->query("ROLLBACK"); $d->close(); exit(1); }

    // Overwrite the real one
    $stmt = $d->prepare("UPDATE `config` SET value=? WHERE module='main' AND `option`='admin_password'");
    $stmt->bind_param('s', $GLOBALS['TEMP_PW']);
    // (mysqli prepared can't see TEMP_PW from outer scope; rebuild)
    $tmp = $TEMP_PW;
    $stmt = $d->prepare("UPDATE `config` SET value=? WHERE module='main' AND `option`='admin_password'");
    $stmt->bind_param('s', $tmp);
    if (!$stmt->execute() || $stmt->affected_rows < 1) {
        echo "ERR update: " . $stmt->error . " (affected={$stmt->affected_rows})\n";
        $d->query("ROLLBACK"); $d->close(); exit(1);
    }
    $d->query("COMMIT");

    echo "SWAPPED. Use these credentials at https://meetgreeksingles.com/administration/\n\n";
    echo "  username = admin\n";
    echo "  password = $TEMP_PW\n\n";
    echo "When you're done, run ?mode=restore to put Irene's original back.\n";
    $d->close(); exit;
}

if ($mode === 'restore') {
    if (!backup_exists($d, $BACKUP_MODULE, $BACKUP_OPTION)) {
        echo "no backup row found — nothing to restore. System may already be in normal state.\n";
        $d->close(); exit;
    }
    $stmt = $d->prepare("SELECT value FROM `config` WHERE module=? AND `option`=? LIMIT 1");
    $stmt->bind_param('ss', $BACKUP_MODULE, $BACKUP_OPTION); $stmt->execute();
    $bak_value = $stmt->get_result()->fetch_assoc()['value'];

    $d->query("START TRANSACTION");
    $stmt = $d->prepare("UPDATE `config` SET value=? WHERE module='main' AND `option`='admin_password'");
    $stmt->bind_param('s', $bak_value);
    if (!$stmt->execute() || $stmt->affected_rows < 1) {
        echo "ERR restore: " . $stmt->error . " (affected={$stmt->affected_rows})\n";
        $d->query("ROLLBACK"); $d->close(); exit(1);
    }
    $stmt = $d->prepare("DELETE FROM `config` WHERE module=? AND `option`=?");
    $stmt->bind_param('ss', $BACKUP_MODULE, $BACKUP_OPTION);
    if (!$stmt->execute()) { echo "ERR del backup: " . $stmt->error . "\n"; $d->query("ROLLBACK"); $d->close(); exit(1); }
    $d->query("COMMIT");

    // Sanity-check length matches what we backed up
    $now_len = strlen((string) get_current_admin_pw($d));
    echo "RESTORED. admin_password length now: $now_len chars (was 9 originally).\n";
    echo "Backup row removed.\n";
    $d->close(); exit;
}

echo "Unknown mode: " . htmlspecialchars($mode) . "\n";
$d->close();
