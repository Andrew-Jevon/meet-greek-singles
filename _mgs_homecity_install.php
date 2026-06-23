<?php
// home_city installer — adds a free-text "Home City" profile field via the
// same user_var pattern M3 used (see _mgs_m3_install.php).
//
// Why a user_var instead of a new userinfo column standalone?  Because the
// Chameleon admin + profile renderer iterate over $g['user_var'] to surface
// fields automatically.  Registering as user_var means the field appears
// everywhere a profile field is normally listed, with no encoded-core
// hooks needed.
//
// Idempotent.  Token-protected.  Delete after each use.

set_time_limit(0);
@ini_set('display_errors', 1);
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }

$g = array();
require __DIR__ . '/_include/config/db.php';
$dbh = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
if ($dbh->connect_errno) { exit("db: " . $dbh->connect_error); }
$dbh->set_charset('utf8mb4');

header('Content-Type: text/plain');

function q($dbh, $sql) {
    if (!$dbh->query($sql)) {
        echo "  ERR: " . $dbh->error . "\n  SQL: " . substr($sql, 0, 160) . "\n";
        return false;
    }
    return true;
}
function col_exists($dbh, $table, $col) {
    $r = $dbh->query("SELECT COUNT(*) c FROM information_schema.columns
        WHERE table_schema=DATABASE() AND table_name='$table' AND column_name='$col'");
    return $r->fetch_assoc()['c'] > 0;
}

echo "home_city installer\n";
echo "===================\n\n";

// 1) userinfo column — VARCHAR(60) is enough for city names worldwide while
//    bounding the storage cost.  Default '' so existing rows are valid.
if (!col_exists($dbh, 'userinfo', 'home_city')) {
    if (q($dbh, "ALTER TABLE userinfo ADD `home_city` VARCHAR(60) NOT NULL DEFAULT ''"))
        echo "  + userinfo.home_city\n";
} else {
    echo "  = userinfo.home_city already exists\n";
}

// 2) config row in module='user_var' so Chameleon recognises the field.
//    type='text' is Chameleon's free-text field type. Shape mirrors existing
//    text-type entries like 'headline' and 'essay': positional 0/1/2 keys
//    (the format Chameleon's admin "Add field" UI writes), 'length' (not
//    'maxlength'), and crucially 'table' => '' — UserFields::checkFiledQuestion
//    ([user_fields.class.php:2704]) reads $data['table'] without isset, raising
//    an E_NOTICE on /join2 if the key is absent (Irene reported 2026-05-03).
//    Empty string is a sentinel meaning "no options table" — text fields don't
//    need one. checkFiledQuestion's next check (`!$data['table']`) returns
//    false for empty, so home_city is correctly excluded from the question
//    flow on join2.
$uvVal = array(
    0                  => 'text',
    1                  => '60',
    2                  => 'Home City',
    'type'             => 'text',
    'table'            => '',               // sentinel — no options table for text fields
    'length'           => '60',
    'title'            => 'Home City',
    'status'           => 'active',
    'group'            => 1,                // 'basic' group — appears alongside
                                            // location fields in profile editor
    'number_values'    => 1,
    'is_searchable'    => 1,                // custom flag — picked up by our
                                            // _list_users_filter.html addition
    'visibility_scope' => 'public',         // public so non-logged visitors and
                                            // search filters can read it
);
$valSerialized = serialize($uvVal);
$valSafe = $dbh->real_escape_string($valSerialized);

$exists = $dbh->query("SELECT id FROM config WHERE module='user_var' AND `option`='home_city'")->num_rows;
if ($exists) {
    if (q($dbh, "UPDATE config SET value='$valSafe' WHERE module='user_var' AND `option`='home_city'"))
        echo "  ~ user_var.home_city config updated\n";
} else {
    // Position right after country/state-equivalent location fields if we can
    // find one; otherwise append.  We don't strictly need a specific position
    // for it to function — the profile editor reads positions for ordering
    // only.
    $maxR = $dbh->query("SELECT IFNULL(MAX(position),0)+1 p FROM config WHERE module='user_var'");
    $pos = $maxR->fetch_assoc()['p'];
    if (q($dbh, "INSERT INTO config (module, `option`, value, show_in_admin, type, position)
                 VALUES ('user_var', 'home_city', '$valSafe', 1, '', $pos)"))
        echo "  + user_var.home_city config inserted (pos=$pos)\n";
}

echo "\nDONE\n";
$dbh->close();
