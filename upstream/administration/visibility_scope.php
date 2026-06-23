<?php
/* M2 admin — edit visibility_scope per profile field.
 *
 * Self-contained: doesn't include administration_start.php (which has an
 * internal whitelist of known admin scripts and redirects unknown ones to
 * profile_view.php). Instead we bootstrap main_start, check the admin role
 * directly, and render a minimal page that mirrors the look of other admin
 * pages without depending on Chameleon's admin chrome.
 */

include("../_include/core/main_start.php");

// Auth: accept BOTH the front-end session (user logged in via /login with
// user.admin = 1) AND the back-end /administration/ session (which stores
// admin_id). One of them must be present and correspond to a user record
// with user.admin = 1.
$_admin_uid = 0;
if (function_exists('guid') && guid() > 0) {
    $is_admin = (int) DB::result("SELECT admin FROM `user` WHERE user_id = " . to_sql((int) guid(), 'Number'));
    if ($is_admin > 0) $_admin_uid = (int) guid();
}
if ($_admin_uid <= 0) {
    // Probe the standard admin-session keys Chameleon uses
    foreach (array('admin_id', 'admin_user_id', 'adm_user_id', 'cur_admin_id') as $k) {
        if (!empty($_SESSION[$k])) {
            $is_admin = (int) DB::result("SELECT admin FROM `user` WHERE user_id = " . to_sql((int) $_SESSION[$k], 'Number'));
            if ($is_admin > 0) { $_admin_uid = (int) $_SESSION[$k]; break; }
        }
    }
}
if ($_admin_uid <= 0) {
    // Send to the admin login page (absolute URL, otherwise the relative
    // 'login' resolves under /administration/ and the prelaunch gate catches
    // the unknown script).
    $host   = $_SERVER['HTTP_HOST'] ?? '';
    $scheme = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ? 'https' : 'http';
    header('Location: ' . $scheme . '://' . $host . '/administration/index.php', true, 302);
    exit;
}

// Save handler
if (get_param('cmd') === 'save') {
    $scopes = get_param('scope', array());
    if (is_array($scopes)) {
        $valid   = array('public', 'member', 'owner');
        $updated = 0;
        foreach ($scopes as $option => $newScope) {
            if (!in_array($newScope, $valid, true)) continue;
            $row = DB::row("SELECT value FROM config
                WHERE module = 'user_var' AND `option` = " . to_sql($option, 'Text') . " LIMIT 1");
            if (!$row) continue;
            $blob = @unserialize($row['value']);
            if (!is_array($blob)) continue;
            $cur = isset($blob['visibility_scope']) ? $blob['visibility_scope'] : 'member';
            if ($cur === $newScope) continue;
            $blob['visibility_scope'] = $newScope;
            DB::execute("UPDATE config SET value = " . to_sql(serialize($blob), 'Text') . "
                WHERE module = 'user_var' AND `option` = " . to_sql($option, 'Text'));
            $updated++;
        }
        $_SESSION['visibility_scope_saved'] = $updated;
    }
    redirect('visibility_scope.php');
}

// Load fields
$fields = array();
DB::query("SELECT `option`, value FROM config WHERE module = 'user_var' ORDER BY position, `option`");
while ($row = DB::fetch_row()) {
    $blob = @unserialize($row['value']);
    if (!is_array($blob)) continue;
    $fields[] = array(
        'key'   => $row['option'],
        'title' => isset($blob['title']) ? $blob['title'] : $row['option'],
        'type'  => isset($blob['type'])  ? $blob['type']  : '',
        'scope' => isset($blob['visibility_scope']) ? $blob['visibility_scope'] : 'member',
    );
}

$saved = 0;
if (isset($_SESSION['visibility_scope_saved'])) {
    $saved = (int) $_SESSION['visibility_scope_saved'];
    unset($_SESSION['visibility_scope_saved']);
}

?><!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Profile field visibility — Meet Greek Singles admin</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; }
        body { font-family: 'Source Sans 3', system-ui, -apple-system, sans-serif;
               background: #f5f5f7; color: #1f2937; margin: 0; padding: 24px;
               line-height: 1.5; }
        .wrap { max-width: 920px; margin: 0 auto; background: #fff;
                border: 1px solid #e6e6ea; border-radius: 14px;
                box-shadow: 0 4px 16px rgba(0,0,0,.04);
                padding: 28px 32px; }
        h1 { margin: 0 0 6px; font-family: 'Playfair Display', Georgia, serif;
             font-weight: 600; font-size: 22px; color: #14487f; }
        .lead { color: #5b6471; font-size: 14px; margin: 0 0 20px; }
        .saved { background: #ecf7ed; border: 1px solid #c8e2c9; color: #2e6b32;
                 padding: 10px 14px; border-radius: 8px; margin-bottom: 16px; font-size: 14px; }
        .nav-back { display: inline-block; color: #2c4a76; text-decoration: none;
                    font-size: 13px; margin-bottom: 16px; }
        .nav-back:hover { text-decoration: underline; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 18px; }
        th, td { padding: 11px 12px; text-align: left;
                 border-bottom: 1px solid #ebebef; font-size: 14px; }
        th { background: #fafafc; font-weight: 600; font-size: 12px;
             color: #5b6471; text-transform: uppercase; letter-spacing: 0.4px; }
        td.field-key { font-size: 12px; color: #999; font-family: ui-monospace, monospace; }
        td.field-type { font-size: 12px; color: #888; }
        select { width: 100%; padding: 7px 10px; border: 1px solid #d1d5db;
                 border-radius: 6px; background: #fff; font-size: 14px; }
        .actions { display: flex; justify-content: flex-end; gap: 10px;
                   padding-top: 12px; border-top: 1px solid #ebebef; }
        button { padding: 10px 22px; border: none; border-radius: 8px;
                 font-weight: 600; font-size: 14px; cursor: pointer; }
        .btn-primary { background: #2c4a76; color: #fff; }
        .btn-primary:hover { background: #1f3a60; }
    </style>
</head>
<body>
    <div class="wrap">
        <a href="<?= htmlspecialchars(Common::getOption('url_main','path') ?: '/') ?>administration/" class="nav-back">&larr; Back to admin home</a>
        <h1>Profile field visibility</h1>
        <p class="lead">
            Decide who sees each profile field on a member's page.
            <strong>Public</strong> = visible to anyone (incl. logged-out visitors).
            <strong>Member</strong> = visible to logged-in members only.
            <strong>Owner</strong> = only the field's owner sees their own value.
        </p>

        <?php if ($saved > 0): ?>
            <div class="saved">Saved <?= (int) $saved ?> field(s).</div>
        <?php endif; ?>

        <form method="POST" action="visibility_scope.php">
            <input type="hidden" name="cmd" value="save" />

            <table>
                <thead>
                    <tr>
                        <th>Field</th>
                        <th style="width: 90px;">Type</th>
                        <th style="width: 200px;">Visibility</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach ($fields as $f): ?>
                        <tr>
                            <td>
                                <strong><?= htmlspecialchars($f['title'], ENT_QUOTES, 'UTF-8') ?></strong>
                                <div class="field-key"><?= htmlspecialchars($f['key'], ENT_QUOTES, 'UTF-8') ?></div>
                            </td>
                            <td class="field-type"><?= htmlspecialchars($f['type'], ENT_QUOTES, 'UTF-8') ?></td>
                            <td>
                                <select name="scope[<?= htmlspecialchars($f['key'], ENT_QUOTES, 'UTF-8') ?>]">
                                    <option value="public" <?= $f['scope'] === 'public' ? 'selected' : '' ?>>Public</option>
                                    <option value="member" <?= $f['scope'] === 'member' ? 'selected' : '' ?>>Member</option>
                                    <option value="owner"  <?= $f['scope'] === 'owner'  ? 'selected' : '' ?>>Owner only</option>
                                </select>
                            </td>
                        </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>

            <div class="actions">
                <button type="submit" class="btn-primary">Save changes</button>
            </div>
        </form>
    </div>
</body>
</html>
