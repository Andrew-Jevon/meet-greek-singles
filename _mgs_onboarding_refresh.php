<?php
// Onboarding refresh — replaces the M3 onboarding question set with Irene's
// 2026-05-04 four. Idempotent.
//
//   Deactivates: relationship_intent, greek_importance, greek_future_plans
//                (status='inactive', is_onboarding=0)  — preserves user data,
//                just removes them from the welcome flow.
//   Demotes:     connection_greece  (is_onboarding=0)  — keeps the field
//                live as a profile + matching field, but out of onboarding.
//   Installs:    looking_for         (radio,    5 opts)
//                culture_importance  (radio,    5 opts)
//                greek_meaning       (checkbox, 6 opts)
//                relocation_openness (radio,    5 opts)
//
// Token-protected. Delete after each use.

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
        echo "  ERR: " . $dbh->error . "\n  SQL: " . substr($sql, 0, 200) . "\n";
        return false;
    }
    return true;
}
function col_exists($dbh, $table, $col) {
    $r = $dbh->query("SELECT COUNT(*) c FROM information_schema.columns
        WHERE table_schema=DATABASE() AND table_name='$table' AND column_name='$col'");
    return $r->fetch_assoc()['c'] > 0;
}
function table_exists($dbh, $table) {
    $r = $dbh->query("SELECT COUNT(*) c FROM information_schema.tables
        WHERE table_schema=DATABASE() AND table_name='$table'");
    return $r->fetch_assoc()['c'] > 0;
}

echo "Onboarding refresh\n";
echo "==================\n\n";

// ── 1. Demote / deactivate the M3 fields ────────────────────────────────────
echo "1. Demote/deactivate existing M3 onboarding fields\n";
echo "--------------------------------------------------\n";

$m3DemoteOnly = array('connection_greece');               // keep active, just off onboarding
$m3Deactivate = array('relationship_intent', 'greek_importance', 'greek_future_plans');

foreach (array_merge($m3DemoteOnly, $m3Deactivate) as $name) {
    $r = $dbh->query("SELECT value FROM config WHERE module='user_var' AND `option`='$name'");
    $row = $r->fetch_assoc();
    if (!$row) { echo "  = $name not found, skipping\n"; continue; }
    $val = @unserialize($row['value']);
    if (!is_array($val)) { echo "  ! $name unserialize failed, skipping\n"; continue; }

    $val['is_onboarding'] = 0;
    if (in_array($name, $m3Deactivate, true)) {
        $val['status'] = 'inactive';
    }
    $safe = $dbh->real_escape_string(serialize($val));
    if (q($dbh, "UPDATE config SET value='$safe' WHERE module='user_var' AND `option`='$name'")) {
        $what = in_array($name, $m3Deactivate, true) ? 'deactivated' : 'demoted (still active as profile field)';
        echo "  ~ $name  → $what\n";
    }
}
echo "\n";

// ── 2. New fields ──────────────────────────────────────────────────────────
echo "2. Install 2026-05-04 onboarding fields\n";
echo "----------------------------------------\n\n";

$fields = array(
    'looking_for' => array(
        'title' => 'What are you looking for?',
        'type'  => 'radio',
        'options' => array(
            'A meaningful, long-term relationship',
            'Marriage',
            'A life partner',
            'Something serious, but let\'s see where it leads',
            'Friendship first',
        ),
    ),
    'culture_importance' => array(
        'title' => 'How important is Greek culture in your life?',
        'type'  => 'radio',
        'options' => array(
            'It\'s a core part of who I am',
            'Very important',
            'Somewhat important',
            'Not very important, but I appreciate it',
            'Not important',
        ),
    ),
    'greek_meaning' => array(
        'title' => 'What does being Greek mean to you?',
        'type'  => 'checkbox',
        'options' => array(
            'Family and traditions',
            'Language and communication',
            'Faith and values',
            'Cultural lifestyle (food, music, celebrations)',
            'Connection to Greece',
            'It\'s part of my identity, but I define it in my own way',
        ),
    ),
    'relocation_openness' => array(
        'title' => 'Do you see yourself open to relocating for the right person?',
        'type'  => 'radio',
        'options' => array(
            'Yes — I\'m open to relocating anywhere',
            'Yes — but preferably within Greece',
            'Yes — but preferably abroad (e.g., Europe, USA, Australia)',
            'Maybe — it depends on the connection',
            'No — I prefer to stay where I am',
        ),
    ),
);

foreach ($fields as $name => $cfg) {
    echo "Field: $name ({$cfg['type']})\n";

    // 2a. var_<name> options table
    $varTable = "var_$name";
    if (!table_exists($dbh, $varTable)) {
        if (q($dbh, "CREATE TABLE `$varTable` (
            id INT(11) NOT NULL AUTO_INCREMENT,
            title VARCHAR(255) NOT NULL DEFAULT '',
            PRIMARY KEY (id)
        ) ENGINE=MyISAM")) echo "  + table $varTable\n";
    } else {
        echo "  = table $varTable already exists\n";
    }
    // Seed options only if empty
    $r = $dbh->query("SELECT COUNT(*) c FROM `$varTable`");
    if ($r->fetch_assoc()['c'] == 0) {
        foreach ($cfg['options'] as $opt) {
            $safe = $dbh->real_escape_string($opt);
            q($dbh, "INSERT INTO `$varTable` (title) VALUES ('$safe')");
        }
        echo "  + seeded " . count($cfg['options']) . " options\n";
    } else {
        echo "  = options already seeded\n";
    }

    // 2b. userinfo column
    if (!col_exists($dbh, 'userinfo', $name)) {
        $colType = ($cfg['type'] === 'checkbox')
            ? 'BIGINT(22) UNSIGNED NOT NULL DEFAULT 0'   // bitmask of selected option IDs
            : 'INT(11) NOT NULL DEFAULT 0';
        if (q($dbh, "ALTER TABLE userinfo ADD `$name` $colType")) echo "  + userinfo.$name\n";
    } else {
        echo "  = userinfo.$name already exists\n";
    }

    // 2c. user_var config row.
    // Shape mirrors existing radio/checkbox entries: positional 0..4 keys
    // (the format Chameleon's admin "Add field" UI writes), plus named keys.
    // Critically includes 'table' => $varTable so UserFields::checkFiledQuestion
    // (user_fields.class.php:2704) doesn't raise an E_NOTICE when iterating
    // user_vars on /join2 — same fix that fell on home_city last round.
    $uvVal = array(
        0                  => 'from_table',
        1                  => $cfg['type'],          // 'radio' or 'checkbox'
        2                  => $varTable,
        3                  => $cfg['title'],
        4                  => 2,                      // group = interests/lifestyle
        'type'             => $cfg['type'],
        'table'            => $varTable,
        'title'            => $cfg['title'],
        'status'           => 'active',
        'group'            => 2,
        'number_values'    => count($cfg['options']),
        'is_onboarding'    => 1,                      // surfaces on /onboarding.php
        'is_searchable'    => 1,                      // matching uses these
        'visibility_scope' => 'member',               // visible after login
    );
    $valSerialized = serialize($uvVal);
    $valSafe = $dbh->real_escape_string($valSerialized);

    $exists = $dbh->query("SELECT id FROM config WHERE module='user_var' AND `option`='$name'")->num_rows;
    if ($exists) {
        if (q($dbh, "UPDATE config SET value='$valSafe' WHERE module='user_var' AND `option`='$name'"))
            echo "  ~ user_var config updated\n";
    } else {
        $maxR = $dbh->query("SELECT IFNULL(MAX(position),0)+1 p FROM config WHERE module='user_var'");
        $pos = $maxR->fetch_assoc()['p'];
        if (q($dbh, "INSERT INTO config (module, `option`, value, show_in_admin, type, position)
                     VALUES ('user_var', '$name', '$valSafe', 1, '', $pos)"))
            echo "  + user_var config inserted (pos=$pos)\n";
    }
    echo "\n";
}

// ── 3. Reset onboarding_done for any test users so they re-enter the flow ──
// Pre-launch only: the new question set is meaningfully different, so even
// users who completed M3 onboarding should be re-prompted with the new four.
echo "3. Reset user.onboarding_done = 0 for all users (pre-launch only)\n";
echo "------------------------------------------------------------------\n";
$r = $dbh->query("SELECT COUNT(*) c FROM user WHERE onboarding_done = 1");
$count = (int) $r->fetch_assoc()['c'];
if (q($dbh, "UPDATE user SET onboarding_done = 0 WHERE onboarding_done = 1")) {
    echo "  ~ reset $count users to onboarding_done=0\n";
}

echo "\nDONE\n";
$dbh->close();
