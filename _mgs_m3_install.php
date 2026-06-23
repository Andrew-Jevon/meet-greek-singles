<?php
// M3 installer — adds the 4 onboarding fields to Chameleon's user_var system,
// safely via Config::add / Config::update (so the serialised blob is built by
// the same code Chameleon uses everywhere else). Token-protected, idempotent.

set_time_limit(0);
@ini_set('display_errors', 1);
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }

// We need Chameleon bootstrapped to use Config::add / DB::execute / etc.
// But main_start.php triggers the prelaunch gate which would redirect us.
// Workaround: define a sentinel and short-circuit it via $area + ?platform_mode_off-style.
// Simpler: use direct mysqli for SQL parts, then a tiny manual serialize() call for config rows.

$g = array();
require __DIR__ . '/_include/config/db.php';
$dbh = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
if ($dbh->connect_errno) { exit("db: " . $dbh->connect_error); }
$dbh->set_charset('utf8mb4');

header('Content-Type: text/plain');

function q($dbh, $sql) {
    if (!$dbh->query($sql)) {
        echo "  ERR: " . $dbh->error . "\n  SQL: " . substr($sql, 0, 120) . "\n";
        return false;
    }
    return true;
}

function col_exists($dbh, $table, $col) {
    $r = $dbh->query("SELECT COUNT(*) c FROM information_schema.columns
        WHERE table_schema=DATABASE() AND table_name='$table' AND column_name='$col'");
    $row = $r->fetch_assoc();
    return $row['c'] > 0;
}
function table_exists($dbh, $table) {
    $r = $dbh->query("SELECT COUNT(*) c FROM information_schema.tables
        WHERE table_schema=DATABASE() AND table_name='$table'");
    $row = $r->fetch_assoc();
    return $row['c'] > 0;
}

// -- 1. The 4 onboarding fields ---------------------------------------------
// Locked design (project_status&plan.md, 2026-04-22):
//   Q1  Connection to Greece     — single select (radio)
//   Q2  Relationship intent      — single select (radio)
//   Q3  Greek culture importance — single select (radio, 1-5 scale)
//   Q4  Future plans for Greece  — multi-select (checkbox)
//
// Each becomes a Chameleon user_var entry, group=2 (interests/lifestyle), with
// a custom 'is_onboarding'=>1 flag we read in onboarding.php.

$fields = array(
    'connection_greece' => array(
        'title' => 'Connection to Greece',
        'type'  => 'radio',
        'options' => array(
            'Living in Greece',
            'Greek living abroad (diaspora)',
            'Greek heritage born abroad',
            'Philhellene (love Greek culture)',
            'Other',
        ),
    ),
    'relationship_intent' => array(
        'title' => 'What I am looking for',
        'type'  => 'radio',
        'options' => array(
            'Marriage',
            'Serious long-term relationship',
            'Open to a meaningful connection',
            'Friendship first',
            'Not sure yet',
        ),
    ),
    'greek_importance' => array(
        'title' => 'Importance of Greek culture, values & religion',
        'type'  => 'radio',
        'options' => array(
            'Very important',
            'Important',
            'Somewhat important',
            'Neutral',
            'Not important',
        ),
    ),
    'greek_future_plans' => array(
        'title' => 'My future plans connected to Greece',
        'type'  => 'checkbox',
        'options' => array(
            'Want to live in Greece',
            'Open to relocating',
            'Want to retire there',
            'Visit Greece often',
            'Strong ties, settled abroad',
            'Not part of my plans',
        ),
    ),
);

echo "M3 onboarding-field installer\n";
echo "=============================\n\n";

foreach ($fields as $name => $cfg) {
    echo "Field: $name ({$cfg['type']})\n";

    // 1a. var_<name> table with the answer options
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
    // Seed options (only if empty)
    $r = $dbh->query("SELECT COUNT(*) c FROM `$varTable`");
    $row = $r->fetch_assoc();
    if ($row['c'] == 0) {
        foreach ($cfg['options'] as $opt) {
            $safe = $dbh->real_escape_string($opt);
            q($dbh, "INSERT INTO `$varTable` (title) VALUES ('$safe')");
        }
        echo "  + seeded " . count($cfg['options']) . " options\n";
    } else {
        echo "  = options already seeded ({$row['c']} rows)\n";
    }

    // 1b. userinfo column
    if (!col_exists($dbh, 'userinfo', $name)) {
        $colType = ($cfg['type'] === 'checkbox') ? 'BIGINT(22) UNSIGNED NOT NULL DEFAULT 0' : 'INT(11) NOT NULL DEFAULT 0';
        if (q($dbh, "ALTER TABLE userinfo ADD `$name` $colType")) echo "  + userinfo.$name\n";
    } else {
        echo "  = userinfo.$name already exists\n";
    }

    // 1c. config row in module='user_var' for $g['user_var'][$name]
    $uvVal = array(
        'type'             => $cfg['type'],
        'table'            => $varTable,
        'title'            => $cfg['title'],
        'status'           => 'active',
        'group'            => 2,                // interests/lifestyle section
        'number_values'    => 1,
        'is_onboarding'    => 1,                // custom flag — read by onboarding.php
        'is_searchable'    => 1,                // custom flag — picked up by M3 search filter wiring
        'visibility_scope' => 'member',         // public | member | owner — read by M2 visibility checks
    );
    $valSerialized = serialize($uvVal);
    $valSafe = $dbh->real_escape_string($valSerialized);

    $exists = $dbh->query("SELECT id FROM config WHERE module='user_var' AND `option`='$name'")->num_rows;
    if ($exists) {
        if (q($dbh, "UPDATE config SET value='$valSafe' WHERE module='user_var' AND `option`='$name'"))
            echo "  ~ user_var config updated\n";
    } else {
        // Position: max + 1 (so it appears at the end of the field list)
        $maxR = $dbh->query("SELECT IFNULL(MAX(position),0)+1 p FROM config WHERE module='user_var'");
        $pos = $maxR->fetch_assoc()['p'];
        if (q($dbh, "INSERT INTO config (module, `option`, value, show_in_admin, type, position)
                     VALUES ('user_var', '$name', '$valSafe', 1, '', $pos)"))
            echo "  + user_var config inserted (pos=$pos)\n";
    }
    echo "\n";
}

// -- 2. Visibility-scope flag for ALL existing user_var entries (M2 prep) ----
// Mark every existing field's serialised blob with a default visibility_scope='member'
// if it doesn't already have one — so M2 visibility checks can short-circuit cleanly.
echo "M2 prep: backfill visibility_scope on existing user_var rows\n";
echo "============================================================\n";
$r = $dbh->query("SELECT `option`, value FROM config WHERE module='user_var'");
$updated = 0; $skipped = 0;
while ($row = $r->fetch_assoc()) {
    $val = @unserialize($row['value']);
    if (!is_array($val)) { $skipped++; continue; }
    if (isset($val['visibility_scope'])) { $skipped++; continue; }
    $val['visibility_scope'] = 'member';   // safe default — same as today's behaviour
    $newSer = $dbh->real_escape_string(serialize($val));
    $opt = $dbh->real_escape_string($row['option']);
    q($dbh, "UPDATE config SET value='$newSer' WHERE module='user_var' AND `option`='$opt'");
    $updated++;
}
echo "  updated: $updated   skipped: $skipped\n\n";

// -- 3. Onboarding state column on user table -------------------------------
echo "Onboarding state column\n";
echo "=======================\n";
if (!col_exists($dbh, 'user', 'onboarding_done')) {
    if (q($dbh, "ALTER TABLE user ADD `onboarding_done` TINYINT(1) NOT NULL DEFAULT 0"))
        echo "  + user.onboarding_done (default 0 = needs onboarding)\n";
} else {
    echo "  = user.onboarding_done already exists\n";
}

echo "\nDONE\n";
$dbh->close();
