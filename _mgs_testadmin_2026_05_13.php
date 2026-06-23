<?php
// One-shot: create a disposable test-admin account for Everett to confirm
// /administration/ login flow, with a built-in cleanup mode to remove it.
//
// Modes (require token):
//   ?token=...                 -> status (default; non-destructive)
//   ?token=...&mode=create     -> insert testadmin row (admin=1, bcrypt pw)
//   ?token=...&mode=cleanup    -> delete that row + its cascade rows
//
// The row is cloned from uid=1 so every NOT-NULL column has a sensible value,
// then overridden for: name, name_seo, mail, password, admin, active,
// ban_global, active_code, social IDs, register, last_visit, avatar.
// userinfo + userpartner rows are also cloned so Chameleon side-tables don't
// look at this user and choke.
set_time_limit(0); @ini_set('display_errors', 1);
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }

$g = array(); require __DIR__ . '/_include/config/db.php';
$d = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
$d->set_charset('utf8mb4');
header('Content-Type: text/plain');

$mode = $_GET['mode'] ?? 'status';

$LOGIN = 'testadmin_20260513';
$MAIL  = 'testadmin@meetgreeksingles.com';
$PLAIN = 'mgsAdmin!2026';

function existing_id(mysqli $d, $login) {
    $stmt = $d->prepare("SELECT user_id FROM `user` WHERE name=?");
    $stmt->bind_param('s', $login); $stmt->execute();
    $r = $stmt->get_result()->fetch_assoc();
    return $r ? (int) $r['user_id'] : null;
}

function clone_row_with_overrides(mysqli $d, $table, $src_id, array $overrides) {
    $stmt = $d->prepare("SELECT * FROM `$table` WHERE user_id=?");
    $stmt->bind_param('i', $src_id); $stmt->execute();
    $row = $stmt->get_result()->fetch_assoc();
    if (!$row) return null;
    foreach ($overrides as $k => $v) {
        if (array_key_exists($k, $row)) $row[$k] = $v;
    }
    return $row;
}

function insert_row(mysqli $d, $table, array $row) {
    $cols = array_keys($row);
    $place = array_fill(0, count($cols), '?');
    $sql = "INSERT INTO `$table` (`" . implode('`,`', $cols) . "`) VALUES (" . implode(',', $place) . ")";
    $stmt = $d->prepare($sql);
    if (!$stmt) return [false, $d->error];
    $types = ''; $vals = [];
    foreach ($row as $v) {
        if (is_int($v)) { $types .= 'i'; }
        elseif (is_float($v)) { $types .= 'd'; }
        elseif (is_null($v)) { $types .= 's'; }
        else { $types .= 's'; }
        $vals[] = $v;
    }
    $stmt->bind_param($types, ...$vals);
    $ok = $stmt->execute();
    return [$ok, $ok ? $d->insert_id : $stmt->error];
}

// -------- status (default) --------
if ($mode === 'status') {
    $tid = existing_id($d, $LOGIN);
    echo "test-admin status: " . ($tid ? "EXISTS (user_id=$tid)" : "absent") . "\n";
    $r = $d->query("SELECT user_id, name, mail, admin, active FROM `user` ORDER BY user_id");
    echo "\ncurrent users:\n";
    while ($row = $r->fetch_assoc()) {
        printf("  uid=%-4s name=%-22s mail=%-30s admin=%s active=%s\n",
            $row['user_id'], $row['name'], $row['mail'], $row['admin'], $row['active']);
    }
    echo "\nUse: ?mode=create  or  ?mode=cleanup\n";
    $d->close(); exit;
}

// -------- create --------
if ($mode === 'create') {
    if (existing_id($d, $LOGIN)) {
        echo "ERR: test-admin '$LOGIN' already exists. Run cleanup first.\n";
        $d->close(); exit(1);
    }
    $now = date('Y-m-d H:i:s');
    $hash = password_hash($PLAIN, PASSWORD_BCRYPT);

    $u = clone_row_with_overrides($d, 'user', 1, [
        'user_id'        => 0,            // auto-increment
        'name'           => $LOGIN,
        'name_seo'       => $LOGIN,
        'mail'           => $MAIL,
        'change_mail'    => '',
        'password'       => $hash,
        'admin'          => 1,
        'active'         => 1,
        'ban_global'     => 0,
        'active_code'    => '',
        'register'       => $now,
        'last_visit'     => $now,
        'avatar'         => 0,
        'is_photo'       => 0,
        'is_photo_public'=> 0,
        'facebook_id'    => 0,
        'google_plus_id' => 0,
        'linkedin_id'    => 0,
        'twitter_id'     => 0,
        'vk_id'          => 0,
        'new_mails'      => 0,
        'new_interests'  => 0,
        'new_views'      => 0,
        'total_views'    => 0,
        'last_ip'        => '',
        'auth_key'       => '',
        'onboarding_done'=> 1,
    ]);
    if (!$u) { echo "ERR: uid=1 not found, cannot clone\n"; $d->close(); exit(1); }

    $d->query("START TRANSACTION");
    [$ok, $idOrErr] = insert_row($d, 'user', $u);
    if (!$ok) { echo "ERR insert user: $idOrErr\n"; $d->query("ROLLBACK"); $d->close(); exit(1); }
    $new_id = (int) $idOrErr;

    foreach (['userinfo', 'userpartner'] as $t) {
        $row = clone_row_with_overrides($d, $t, 1, ['user_id' => $new_id]);
        if ($row === null) continue;  // table might be empty
        [$ok, $err] = insert_row($d, $t, $row);
        if (!$ok) { echo "ERR insert $t: $err\n"; $d->query("ROLLBACK"); $d->close(); exit(1); }
    }

    // Verify password round-trip
    $stmt = $d->prepare("SELECT password FROM `user` WHERE user_id=?");
    $stmt->bind_param('i', $new_id); $stmt->execute();
    $stored = $stmt->get_result()->fetch_assoc()['password'];
    if (!password_verify($PLAIN, $stored)) {
        echo "ERR password_verify failed\n"; $d->query("ROLLBACK"); $d->close(); exit(1);
    }

    $d->query("COMMIT");

    echo "CREATED\n";
    echo "  user_id  = $new_id\n";
    echo "  login    = $LOGIN\n";
    echo "  password = $PLAIN\n";
    echo "  mail     = $MAIL\n";
    echo "  admin    = 1\n";
    echo "\nLog in at: https://meetgreeksingles.com/administration/\n";
    echo "When done, run with ?mode=cleanup to remove this row.\n";
    $d->close(); exit;
}

// -------- cleanup --------
if ($mode === 'cleanup') {
    $tid = existing_id($d, $LOGIN);
    if (!$tid) { echo "test-admin '$LOGIN' not found — nothing to clean up.\n"; $d->close(); exit; }
    if ($tid === 1) { echo "REFUSE: '$LOGIN' resolved to uid=1 — aborting (won't touch Joyce).\n"; $d->close(); exit(1); }

    $d->query("START TRANSACTION");
    foreach (['userinfo', 'userpartner', 'user'] as $t) {
        $stmt = $d->prepare("DELETE FROM `$t` WHERE user_id=?");
        $stmt->bind_param('i', $tid);
        $ok = $stmt->execute();
        if (!$ok) { echo "ERR delete $t: " . $stmt->error . "\n"; $d->query("ROLLBACK"); $d->close(); exit(1); }
        printf("  %-15s deleted %d row(s)\n", $t, $stmt->affected_rows);
    }
    // Safety: uid=1 still exists?
    $r = $d->query("SELECT COUNT(*) c FROM `user` WHERE user_id=1");
    if ((int) $r->fetch_assoc()['c'] !== 1) {
        echo "SAFETY: uid=1 disappeared — rolling back.\n";
        $d->query("ROLLBACK"); $d->close(); exit(1);
    }
    $d->query("COMMIT");

    $r = $d->query("SELECT COUNT(*) c FROM `user`");
    echo "\nremaining users: " . $r->fetch_assoc()['c'] . "\nDONE\n";
    $d->close(); exit;
}

echo "Unknown mode: " . htmlspecialchars($mode) . "\n";
$d->close();
