<?php
// M3 update — apply Irene's 2026-04-25 onboarding outline.
// Token-protected, idempotent.
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }
set_time_limit(0); @ini_set('display_errors', 1);

$g = array(); require __DIR__ . '/_include/config/db.php';
$dbh = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
if ($dbh->connect_errno) exit("db: " . $dbh->connect_error);
$dbh->set_charset('utf8mb4');
header('Content-Type: text/plain');

function q($dbh, $sql) {
    if (!$dbh->query($sql)) { echo "  ERR: " . $dbh->error . "\n  SQL: " . substr($sql,0,150) . "\n"; return false; }
    return true;
}

// Final spec from Irene 2026-04-25:
$fields = array(
    'connection_greece' => array(
        'title'    => 'How do you connect with Greece?',
        'subtitle' => 'We celebrate every kind of Greek connection.',
        'type'     => 'radio',
        'options'  => array(
            'Born and raised in Greece',
            'Greek, living abroad (diaspora)',
            'Greek heritage / roots',
            'Philhellene (love Greek culture)',
        ),
    ),
    'relationship_intent' => array(
        'title'    => 'What are you hoping to find?',
        'subtitle' => "Let's start with your intention.",
        'type'     => 'radio',
        'options'  => array(
            'A serious relationship',
            'Something meaningful, but open',
            'Friendship first',
            'Just exploring',
        ),
    ),
    'greek_importance' => array(
        'title'    => 'How important is Greek culture in your life?',
        'subtitle' => 'Your connection to your roots matters.',
        'type'     => 'radio',
        'options'  => array(
            "Very important – it's part of who I am",
            'Important, but not everything',
            'Somewhat important',
            'Not a big factor for me',
        ),
    ),
    // Q4 swapped: was greek_future_plans (checkbox/multi). Now greek_values_traditions (radio).
    'greek_values_traditions' => array(
        'title'    => 'Do shared values and traditions matter to you?',
        'subtitle' => 'Compatibility goes beyond attraction.',
        'type'     => 'radio',
        'options'  => array(
            'Very important',
            'Somewhat important',
            'Not very important',
        ),
    ),
);

echo "M3 update — apply Irene's onboarding outline\n";
echo "============================================\n\n";

// Drop the old greek_future_plans field cleanly (column, var_ table, user_var row)
echo "Removing old greek_future_plans field\n";
q($dbh, "DROP TABLE IF EXISTS `var_greek_future_plans`");
$colExists = $dbh->query("SELECT COUNT(*) c FROM information_schema.columns
    WHERE table_schema=DATABASE() AND table_name='userinfo' AND column_name='greek_future_plans'")
    ->fetch_assoc()['c'];
if ($colExists) q($dbh, "ALTER TABLE userinfo DROP COLUMN `greek_future_plans`");
q($dbh, "DELETE FROM config WHERE module='user_var' AND `option`='greek_future_plans'");
echo "  removed.\n\n";

foreach ($fields as $name => $cfg) {
    echo "Field: $name ({$cfg['type']})\n";
    $varTable = "var_$name";

    // var_<name> table
    $exists = $dbh->query("SELECT COUNT(*) c FROM information_schema.tables
        WHERE table_schema=DATABASE() AND table_name='$varTable'")->fetch_assoc()['c'];
    if (!$exists) {
        q($dbh, "CREATE TABLE `$varTable` (
            id INT(11) NOT NULL AUTO_INCREMENT,
            title VARCHAR(255) NOT NULL DEFAULT '',
            PRIMARY KEY (id)
        ) ENGINE=MyISAM");
        echo "  + created $varTable\n";
    }

    // Refresh option list — truncate + reinsert in order (keeps ids stable across deploys)
    q($dbh, "TRUNCATE TABLE `$varTable`");
    foreach ($cfg['options'] as $opt) {
        $safe = $dbh->real_escape_string($opt);
        q($dbh, "INSERT INTO `$varTable` (title) VALUES ('$safe')");
    }
    echo "  ~ reseeded " . count($cfg['options']) . " options\n";

    // userinfo column
    $colExists = $dbh->query("SELECT COUNT(*) c FROM information_schema.columns
        WHERE table_schema=DATABASE() AND table_name='userinfo' AND column_name='$name'")
        ->fetch_assoc()['c'];
    if (!$colExists) {
        q($dbh, "ALTER TABLE userinfo ADD `$name` INT(11) NOT NULL DEFAULT 0");
        echo "  + userinfo.$name\n";
    }

    // user_var config blob (replace title + subtitle + type)
    $val = array(
        'type'             => $cfg['type'],
        'table'            => $varTable,
        'title'            => $cfg['title'],
        'subtitle'         => $cfg['subtitle'],
        'status'           => 'active',
        'group'            => 2,
        'number_values'    => 1,
        'is_onboarding'    => 1,
        'is_searchable'    => 1,
        'visibility_scope' => 'member',
    );
    $valSafe = $dbh->real_escape_string(serialize($val));

    $row = $dbh->query("SELECT id FROM config WHERE module='user_var' AND `option`='$name'")->num_rows;
    if ($row) {
        q($dbh, "UPDATE config SET value='$valSafe' WHERE module='user_var' AND `option`='$name'");
        echo "  ~ user_var config updated\n";
    } else {
        $pos = $dbh->query("SELECT IFNULL(MAX(position),0)+1 p FROM config WHERE module='user_var'")
            ->fetch_assoc()['p'];
        q($dbh, "INSERT INTO config (module, `option`, value, show_in_admin, type, position)
                 VALUES ('user_var', '$name', '$valSafe', 1, '', $pos)");
        echo "  + user_var config inserted (pos=$pos)\n";
    }
    echo "\n";
}

// Reset onboarding_done so existing test traffic gets to see the new flow.
echo "Reset onboarding_done = 0 for users with no answers yet\n";
q($dbh, "UPDATE user u
    LEFT JOIN userinfo i ON i.user_id = u.user_id
    SET u.onboarding_done = 0
    WHERE COALESCE(i.connection_greece, 0) = 0
      AND COALESCE(i.relationship_intent, 0) = 0
      AND COALESCE(i.greek_importance, 0) = 0
      AND COALESCE(i.greek_values_traditions, 0) = 0
      AND u.onboarding_done = 1");
echo "  done.\n";

echo "\nDONE\n";
$dbh->close();
