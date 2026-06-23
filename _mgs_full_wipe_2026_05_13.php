<?php
// One-shot: wipe ALL remaining user data (uid=1 included) + generate and
// install a fresh random admin_password.
//
// Modes:
//   ?token=...                -> dry-run report
//   ?token=...&execute=1      -> actually wipe + rotate password
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

$targets = array(
    'adv_cars','adv_casting','adv_film','adv_housting','adv_items','adv_jobs','adv_music',
    'adv_myspace','adv_personals','adv_sale','adv_services','app_push_tokens','audio_greeting',
    'blogs_comment','blogs_comments_likes','blogs_post','blogs_post_likes','city_avatar_face',
    'city_live_streaming','city_photo','city_users','contact','custom_event_applications',
    'events_event','events_event_comment','events_event_comment_comment','events_event_guest',
    'events_event_image','events_setting','flashchat_messages','flashchat_users','forum_message',
    'forum_read_marker','forum_setting','forum_topic','friends','friends_requests','gallery_albums',
    'gallery_comments','gallery_images','groups_forum','groups_forum_comment',
    'groups_forum_comment_comment','groups_group','groups_group_comment',
    'groups_group_comment_comment','groups_group_image','groups_group_member','groups_invite',
    'groups_setting','groups_social','groups_social_subscribers','groups_user_block_list',
    'im_audio_message','im_contact_replied','interests','invites','live_streaming',
    'live_streaming_viewers','mail_folder','mail_msg','meta_link_info','music_musician',
    'music_musician_comment','music_musician_image','music_musician_vote','music_setting',
    'music_song','music_song_comment','music_song_image','music_song_vote','outside_image',
    'payment_before','payment_log','photo','photo_comments','photo_comments_likes',
    'photo_face_user_relation','photo_likes','photo_rate','places_place','places_place_image',
    'places_place_vote','places_review','places_review_vote','profile_status','search_save',
    'spotlight','stickers_popularity_users','texts','userinfo','userpartner','users_checkbox',
    'users_comments','users_flash','users_private_note','user_interests','vids_comment',
    'vids_comments_likes','vids_likes','vids_rate','vids_video','wall','wall_comments',
    'wall_comments_likes','wall_comments_viewed','wall_items_for_user','wall_likes','wall_stats',
    'widgets','user',
);

function rowcount(mysqli $d, $t) {
    $r = $d->query("SELECT COUNT(*) c FROM `$t`");
    return $r ? (int) $r->fetch_assoc()['c'] : 'ERR';
}
function gen_pw($len = 12) {
    // Avoid ambiguous chars (0,O,1,l,I).
    $alpha = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789';
    $special = '!@#';
    $out = '';
    for ($i = 0; $i < $len - 2; $i++) {
        $out .= $alpha[random_int(0, strlen($alpha) - 1)];
    }
    $out .= $special[random_int(0, strlen($special) - 1)];
    $out .= (string) random_int(2, 9);
    return $out;
}

if (!$DRY_RUN) $d->query("START TRANSACTION");

echo str_pad('TABLE', 36) . str_pad('BEFORE', 9) . "AFTER\n";
echo str_repeat('-', 56) . "\n";
$total_deleted = 0;
foreach ($targets as $t) {
    $before = rowcount($d, $t);
    if (!is_int($before)) { printf("%-36s %s\n", $t, $before); continue; }
    if ($DRY_RUN) {
        printf("%-36s %-9d (dry run)\n", $t, $before);
        $total_deleted += $before;
        continue;
    }
    if ($before > 0) {
        if (!$d->query("DELETE FROM `$t`")) {
            printf("%-36s ERR: %s\n", $t, $d->error);
            $d->query("ROLLBACK"); $d->close(); exit(1);
        }
    }
    $after = rowcount($d, $t);
    $total_deleted += ($before - $after);
    printf("%-36s %-9d %d\n", $t, $before, $after);
}

echo "\nRotating admin_password in `config` (id=46)...\n";
if ($DRY_RUN) {
    echo "  would generate fresh random pw and UPDATE config.value\n";
} else {
    $pw = gen_pw(12);
    $stmt = $d->prepare("UPDATE `config` SET value=? WHERE module='main' AND `option`='admin_password'");
    $stmt->bind_param('s', $pw);
    if (!$stmt->execute() || $stmt->affected_rows < 1) {
        echo "  ERR: " . $stmt->error . " affected=" . $stmt->affected_rows . "\n";
        $d->query("ROLLBACK"); $d->close(); exit(1);
    }

    // Sanity check
    $r = $d->query("SELECT value FROM `config` WHERE module='main' AND `option`='admin_password'");
    $stored = $r->fetch_assoc()['value'];
    if ($stored !== $pw) {
        echo "  ERR: stored value doesn't match generated. aborting.\n";
        $d->query("ROLLBACK"); $d->close(); exit(1);
    }
}

if (!$DRY_RUN) {
    // Verify user table is empty before commit
    if (rowcount($d, 'user') !== 0) {
        echo "\nSAFETY: user table not empty — rolling back.\n";
        $d->query("ROLLBACK"); $d->close(); exit(1);
    }
    $d->query("COMMIT");
    echo "  rotated.\n";
}

echo "\n== Summary ==\n";
echo "  rows deleted:    $total_deleted\n";
echo "  remaining users: " . rowcount($d, 'user') . "\n";
if (!$DRY_RUN) {
    echo "\n*** NEW ADMIN DASHBOARD CREDENTIALS — copy now, only printed once ***\n";
    echo "  URL:      https://meetgreeksingles.com/administration/\n";
    echo "  username: admin\n";
    echo "  password: $pw\n";
}

echo "\nDONE\n";
$d->close();
