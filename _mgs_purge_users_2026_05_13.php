<?php
// One-shot purge: delete every user except uid=1, cascade across all known
// user-linked tables, and restore uid=1's admin flag.
//
// Guards:
//   - Token (matches all other _mgs_*.php scripts)
//   - Requires ?execute=1 in addition to token; otherwise dry-run that just
//     reports what WOULD happen.
//   - Wrapped in a transaction (effective for InnoDB tables; harmless for MyISAM).
//   - Refuses to commit if uid=1 row would not exist afterwards.
//
// Idempotent. Safe to run twice.
set_time_limit(0); @ini_set('display_errors', 1);
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }
$DRY_RUN = (($_GET['execute'] ?? '') !== '1');

$g = array(); require __DIR__ . '/_include/config/db.php';
$d = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
$d->set_charset('utf8mb4');
header('Content-Type: text/plain');

echo $DRY_RUN ? "MODE: DRY RUN  (add &execute=1 to actually run)\n\n"
              : "MODE: EXECUTE  (changes will be committed)\n\n";

// (table, primary user-fk col, optional second col for two-party tables)
$targets = array(
    array('adv_cars', 'user_id'),
    array('adv_casting', 'user_id'),
    array('adv_film', 'user_id'),
    array('adv_housting', 'user_id'),
    array('adv_items', 'user_id'),
    array('adv_jobs', 'user_id'),
    array('adv_music', 'user_id'),
    array('adv_myspace', 'user_id'),
    array('adv_personals', 'user_id'),
    array('adv_sale', 'user_id'),
    array('adv_services', 'user_id'),
    array('app_push_tokens', 'user_id'),
    array('audio_greeting', 'user_id'),
    array('blogs_comment', 'user_id'),
    array('blogs_comments_likes', 'user_id'),
    array('blogs_post', 'user_id'),
    array('blogs_post_likes', 'user_id'),
    array('city_avatar_face', 'user_id'),
    array('city_live_streaming', 'user_id'),
    array('city_photo', 'user_id'),
    array('city_users', 'user_id'),
    array('contact', 'user_id'),
    array('custom_event_applications', 'user_id'),
    array('events_event', 'user_id'),
    array('events_event_comment', 'user_id'),
    array('events_event_comment_comment', 'user_id'),
    array('events_event_guest', 'user_id'),
    array('events_event_image', 'user_id'),
    array('events_setting', 'user_id'),
    array('flashchat_messages', 'user_id'),
    array('flashchat_users', 'user_id'),
    array('forum_message', 'user_id'),
    array('forum_read_marker', 'user_id'),
    array('forum_setting', 'user_id'),
    array('forum_topic', 'user_id'),
    array('friends', 'user_id'),
    array('friends_requests', 'user_id'),
    array('gallery_albums', 'user_id'),
    array('gallery_comments', 'user_id'),
    array('gallery_images', 'user_id'),
    array('groups_forum', 'user_id'),
    array('groups_forum_comment', 'user_id'),
    array('groups_forum_comment_comment', 'user_id'),
    array('groups_group', 'user_id'),
    array('groups_group_comment', 'user_id'),
    array('groups_group_comment_comment', 'user_id'),
    array('groups_group_image', 'user_id'),
    array('groups_group_member', 'user_id'),
    array('groups_invite', 'user_id'),
    array('groups_setting', 'user_id'),
    array('groups_social', 'user_id'),
    array('groups_social_subscribers', 'user_id'),
    array('groups_user_block_list', 'user_id'),
    array('im_audio_message', 'user_id'),
    array('im_contact_replied', 'user_id'),
    array('interests', 'user_id'),
    array('invites', 'user_id'),
    array('live_streaming', 'user_id'),
    array('live_streaming_viewers', 'user_id'),
    array('mail_folder', 'user_id'),
    array('mail_msg', 'user_id'),
    array('meta_link_info', 'user_id'),
    array('music_musician', 'user_id'),
    array('music_musician_comment', 'user_id'),
    array('music_musician_image', 'user_id'),
    array('music_musician_vote', 'user_id'),
    array('music_setting', 'user_id'),
    array('music_song', 'user_id'),
    array('music_song_comment', 'user_id'),
    array('music_song_image', 'user_id'),
    array('music_song_vote', 'user_id'),
    array('outside_image', 'user_id'),
    array('payment_before', 'user_id'),
    array('payment_log', 'user_id'),
    array('photo', 'user_id'),
    array('photo_comments', 'user_id'),
    array('photo_comments_likes', 'user_id'),
    array('photo_face_user_relation', 'user_id'),
    array('photo_likes', 'user_id'),
    array('photo_rate', 'user_id'),
    array('places_place', 'user_id'),
    array('places_place_image', 'user_id'),
    array('places_place_vote', 'user_id'),
    array('places_review', 'user_id'),
    array('places_review_vote', 'user_id'),
    array('profile_status', 'user_id'),
    array('search_save', 'user_id'),
    array('spotlight', 'user_id'),
    array('stickers_popularity_users', 'user_id'),
    array('texts', 'user_id'),
    array('userinfo', 'user_id'),
    array('userpartner', 'user_id'),
    array('users_checkbox', 'user_id'),
    array('users_comments', 'user_id', 'from_user_id'),
    array('users_flash', 'user_id'),
    array('users_private_note', 'user_id', 'from_user_id'),
    array('user_interests', 'user_id'),
    array('vids_comment', 'user_id'),
    array('vids_comments_likes', 'user_id'),
    array('vids_likes', 'user_id'),
    array('vids_rate', 'user_id'),
    array('vids_video', 'user_id'),
    array('wall', 'user_id'),
    array('wall_comments', 'user_id'),
    array('wall_comments_likes', 'user_id'),
    array('wall_comments_viewed', 'user_id'),
    array('wall_items_for_user', 'user_id'),
    array('wall_likes', 'user_id'),
    array('wall_stats', 'user_id'),
    array('widgets', 'user_id'),
);

function rowcount(mysqli $d, $t) {
    $r = $d->query("SELECT COUNT(*) c FROM `$t`");
    if (!$r) return 'ERR(' . $d->error . ')';
    $row = $r->fetch_assoc();
    return (int) $row['c'];
}

if (!$DRY_RUN) {
    $d->query("START TRANSACTION");
}

echo str_pad('TABLE', 36) . str_pad('BEFORE', 9) . str_pad('TO DELETE', 11) . "AFTER\n";
echo str_repeat('-', 64) . "\n";

$total_deleted = 0;
foreach ($targets as $row) {
    $t = $row[0]; $c1 = $row[1]; $c2 = $row[2] ?? null;

    $before = rowcount($d, $t);
    if (!is_int($before)) { printf("%-36s %s\n", $t, $before); continue; }

    $where = $c2
        ? "`$c1` <> 1 OR `$c2` <> 1"
        : "`$c1` <> 1";
    $count_sql = "SELECT COUNT(*) c FROM `$t` WHERE $where";
    $r = $d->query($count_sql);
    if (!$r) { printf("%-36s %-9s ERR(%s)\n", $t, $before, $d->error); continue; }
    $to_delete = (int) $r->fetch_assoc()['c'];

    if ($DRY_RUN) {
        printf("%-36s %-9d %-11d %s\n", $t, $before, $to_delete, '(dry run)');
        continue;
    }

    if ($to_delete > 0) {
        $ok = $d->query("DELETE FROM `$t` WHERE $where");
        if (!$ok) {
            printf("%-36s %-9d %-11d ERR: %s\n", $t, $before, $to_delete, $d->error);
            $d->query("ROLLBACK");
            echo "\nABORTED — rolled back.\n";
            $d->close(); exit(1);
        }
    }
    $after = rowcount($d, $t);
    $total_deleted += $to_delete;
    printf("%-36s %-9d %-11d %d\n", $t, $before, $to_delete, $after);
}

// Now the user table itself.
$before = rowcount($d, 'user');
$to_delete = (int) $d->query("SELECT COUNT(*) c FROM `user` WHERE user_id <> 1")->fetch_assoc()['c'];
if ($DRY_RUN) {
    printf("%-36s %-9d %-11d %s\n", 'user', $before, $to_delete, '(dry run)');
} else {
    $ok = $d->query("DELETE FROM `user` WHERE user_id <> 1");
    if (!$ok) {
        printf("%-36s ERR: %s\n", 'user', $d->error);
        $d->query("ROLLBACK");
        echo "\nABORTED — rolled back.\n";
        $d->close(); exit(1);
    }
    $after = rowcount($d, 'user');
    $total_deleted += $to_delete;
    printf("%-36s %-9d %-11d %d\n", 'user', $before, $to_delete, $after);
}

echo "\n";

// Restore uid=1 admin flag.
echo "Restoring uid=1 admin flag...\n";
if ($DRY_RUN) {
    $r = $d->query("SELECT admin, role FROM `user` WHERE user_id=1");
    $row = $r ? $r->fetch_assoc() : null;
    if ($row) {
        echo "  current: admin={$row['admin']}  role={$row['role']}\n";
        echo "  would set: admin=1\n";
    } else {
        echo "  uid=1 NOT FOUND\n";
    }
} else {
    $ok = $d->query("UPDATE `user` SET admin = 1 WHERE user_id = 1");
    if (!$ok) {
        printf("  ERR: %s\n", $d->error);
        $d->query("ROLLBACK");
        echo "ABORTED — rolled back.\n";
        $d->close(); exit(1);
    }
    $r = $d->query("SELECT admin, role FROM `user` WHERE user_id=1");
    $row = $r ? $r->fetch_assoc() : null;
    echo "  new: admin={$row['admin']}  role={$row['role']}\n";
}

// Safety check: uid=1 must still exist before commit.
if (!$DRY_RUN) {
    $r = $d->query("SELECT COUNT(*) c FROM `user` WHERE user_id=1");
    $still = (int) $r->fetch_assoc()['c'];
    if ($still !== 1) {
        $d->query("ROLLBACK");
        echo "\nSAFETY: uid=1 missing after deletes — rolled back.\n";
        $d->close(); exit(1);
    }
    $d->query("COMMIT");
    echo "\nCOMMITTED.\n";
}

echo "\n== Summary ==\n";
echo "  rows deleted: $total_deleted\n";
echo "  remaining users: " . rowcount($d, 'user') . "\n";

echo "\nDONE\n";
$d->close();
