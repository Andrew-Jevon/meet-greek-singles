<?php
// READ-ONLY audit of the user table prior to a bulk delete.
// Inventories: counts, admin rows, uid=1 detail, related FK tables.
// No INSERT / UPDATE / DELETE in this script.
set_time_limit(0); @ini_set('display_errors', 1);
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }
$g = array(); require __DIR__ . '/_include/config/db.php';
$d = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
$d->set_charset('utf8mb4');
header('Content-Type: text/plain');

function safe_mail($m) {
    if (!$m) return '';
    $at = strpos($m, '@');
    if ($at === false) return substr($m, 0, 2) . '***';
    return substr($m, 0, 2) . '***' . substr($m, $at);
}
function pw_kind($p) {
    if (!$p) return 'empty';
    if (preg_match('/^\$2[aby]\$/', $p)) return 'bcrypt';
    if (strlen($p) === 32 && ctype_xdigit($p)) return 'md5';
    if (strlen($p) === 40 && ctype_xdigit($p)) return 'sha1';
    return 'other(len=' . strlen($p) . ')';
}

echo "== user table column list ==\n";
$r = $d->query("SHOW COLUMNS FROM `user`");
$cols = array();
while ($r && $row = $r->fetch_assoc()) {
    $cols[] = $row['Field'];
}
echo "  " . implode(', ', $cols) . "\n";

echo "\n== Counts ==\n";
$row = $d->query("SELECT COUNT(*) c FROM `user`")->fetch_assoc();
echo "  total users:           {$row['c']}\n";
$row = $d->query("SELECT COUNT(*) c FROM `user` WHERE admin <> 0")->fetch_assoc();
echo "  admin <> 0:            {$row['c']}\n";
$row = $d->query("SELECT COUNT(*) c FROM `user` WHERE ban_global <> 0")->fetch_assoc();
echo "  ban_global <> 0:       {$row['c']}\n";
$row = $d->query("SELECT COUNT(*) c FROM `user` WHERE active = 0 OR active IS NULL")->fetch_assoc();
echo "  active = 0:            {$row['c']}\n";
$row = $d->query("SELECT COUNT(*) c FROM `user` WHERE active_code IS NOT NULL AND active_code <> ''")->fetch_assoc();
echo "  unconfirmed email:     {$row['c']}\n";

echo "\n== uid=1 detail (admin reference row) ==\n";
$r = $d->query("SELECT user_id, name, mail, admin, active, ban_global, active_code, password, register FROM `user` WHERE user_id=1");
$u1 = $r ? $r->fetch_assoc() : null;
if (!$u1) {
    echo "  ! uid=1 NOT FOUND\n";
} else {
    echo "  user_id     = {$u1['user_id']}\n";
    echo "  name        = '{$u1['name']}'\n";
    echo "  mail        = " . safe_mail($u1['mail']) . "\n";
    echo "  admin       = {$u1['admin']}\n";
    echo "  active      = {$u1['active']}\n";
    echo "  ban_global  = {$u1['ban_global']}\n";
    echo "  active_code = " . ($u1['active_code'] === '' || $u1['active_code'] === null ? '(empty)' : 'SET') . "\n";
    echo "  password    = " . pw_kind($u1['password']) . "\n";
    echo "  register    = {$u1['register']}\n";
}

echo "\n== All admin <> 0 rows (full list — these MUST be preserved) ==\n";
$r = $d->query("SELECT user_id, name, mail, admin, active, ban_global FROM `user` WHERE admin <> 0 ORDER BY user_id");
$admin_ids = array();
while ($r && $row = $r->fetch_assoc()) {
    $admin_ids[] = (int) $row['user_id'];
    echo "  uid={$row['user_id']}  name='{$row['name']}'  mail=" . safe_mail($row['mail']) .
         "  admin={$row['admin']}  active={$row['active']}  ban={$row['ban_global']}\n";
}
echo "  -> admin_ids = [" . implode(',', $admin_ids) . "]\n";

echo "\n== Rows where name='admin' (alt admin convention) ==\n";
$stmt = $d->prepare("SELECT user_id, name, mail, admin, active FROM `user` WHERE name='admin'");
$stmt->execute(); $rs = $stmt->get_result();
while ($row = $rs->fetch_assoc()) {
    echo "  uid={$row['user_id']}  name='{$row['name']}'  mail=" . safe_mail($row['mail']) .
         "  admin={$row['admin']}  active={$row['active']}\n";
}

echo "\n== Last 20 users registered (most recent first) ==\n";
$r = $d->query("SELECT user_id, name, mail, admin, active, register FROM `user` ORDER BY user_id DESC LIMIT 20");
printf("  %-6s  %-22s  %-26s  %-6s  %-7s  %s\n", "uid", "name", "mail", "admin", "active", "register");
while ($r && $row = $r->fetch_assoc()) {
    printf("  %-6s  %-22s  %-26s  %-6s  %-7s  %s\n",
        $row['user_id'], substr($row['name'], 0, 22), safe_mail($row['mail']),
        $row['admin'], $row['active'], $row['register']);
}

echo "\n== Tables with a user_id column (candidates for cascade) ==\n";
$db = $g['db']['db'];
$stmt = $d->prepare("SELECT table_name, column_name FROM information_schema.columns
    WHERE table_schema = ? AND column_name IN ('user_id','from_user_id','to_user_id','owner_id','sender_id','recipient_id')
    ORDER BY table_name, column_name");
$stmt->bind_param('s', $db); $stmt->execute(); $rs = $stmt->get_result();
$tables_with_userfk = array();
while ($row = $rs->fetch_assoc()) {
    $tables_with_userfk[] = $row;
    echo "  {$row['table_name']}.{$row['column_name']}\n";
}

echo "\n== Row counts in those tables (current size) ==\n";
$seen = array();
foreach ($tables_with_userfk as $t) {
    if (isset($seen[$t['table_name']])) continue;
    $seen[$t['table_name']] = true;
    $tn = $t['table_name'];
    $r = $d->query("SELECT COUNT(*) c FROM `$tn`");
    if ($r) {
        $row = $r->fetch_assoc();
        echo "  $tn: {$row['c']}\n";
    }
}

echo "\nDONE\n";
$d->close();
