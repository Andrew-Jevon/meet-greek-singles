<?php
/* Milestone 3 — onboarding gate.
 *
 * Hooked from Common::setSiteOptions(). For logged-in users with
 * user.onboarding_done = 0, bounces every request that isn't part of the
 * onboarding/auth/static surface to /onboarding.php — so the 4-question flow
 * runs before any forced-photo / forced-about prompt fires.
 */

class Onboarding
{
    /** Scripts (basenames) that an unfinished user MAY visit without being bounced. */
    private static $allow = array(
        'onboarding.php',
        // Auth + session lifecycle
        'login.php', 'logout.php', 'ajax.php',
        'forget_password.php', 'confirm_email.php', 'email_not_confirmed.php',
        // Static + utility
        'css.php', 'js.php', 'tmpl_img_loader.php', 'files_uploader.php',
        'favicon.ico', 'robots.txt',
        // Registration finishers — user might be coming back to complete signup
        'join.php', 'join2.php', 'join3.php', 'social_login.php',
    );

    public static function apply()
    {
        // Never gate logout requests — and proactively kill the persistent
        // _c_user / _c_password "remember me" cookies so Chameleon's auto-
        // login can't immediately re-authenticate the user mid-logout.
        if (function_exists('get_param') && get_param('cmd') === 'logout') {
            self::clearRememberMeCookies();
            return;
        }

        // setSiteOptions runs before $g_user is populated, so guid() can return 0.
        // Use Chameleon's session helper (the same one Prelaunch uses) instead.
        $uid = (int) (function_exists('get_session') ? get_session('user_id') : 0);
        if ($uid <= 0 && function_exists('guid')) $uid = (int) guid();
        if ($uid <= 0) return;

        // Look up onboarding_done early so we can suppress force-photo for the
        // entire request when onboarding is still pending. Without this,
        // Chameleon's encoded `forced_profile_picture_upload` flow redirects
        // photoless users to /profile_view.php?show=photos, which triggers
        // setSiteOptions again, which bounces them back to /onboarding.php —
        // a redirect loop (ERR_TOO_MANY_REDIRECTS).
        $row = DB::row("SELECT onboarding_done FROM user WHERE user_id = " . to_sql($uid, 'Number'));
        if (!$row || !array_key_exists('onboarding_done', $row)) return;
        $done = (int) $row['onboarding_done'];

        if ($done === 0) {
            global $g;
            // Disable force-photo + min-photos-to-use-site for THIS REQUEST only.
            // Once the user submits the onboarding form and onboarding_done flips
            // to 1, these settings resume at their normal values from the DB.
            if (isset($g['options'])) {
                $g['options']['forced_profile_picture_upload'] = 'N';
                $g['options']['min_number_photos_to_use_site'] = 0;
            }
        }

        $script = self::currentScript();
        if (in_array($script, self::$allow, true)) return;

        // Admin area never gated. Path check first because Common::isAdminSitePart()
        // has an internal allowlist that doesn't recognise admin pages we add
        // ourselves (e.g. M2 visibility_scope.php).
        if (strpos($_SERVER['SCRIPT_NAME'] ?? '', '/administration/') !== false) return;
        if (method_exists('Common', 'isAdminSitePart') && Common::isAdminSitePart()) return;

        if ($done === 1) return;

        // Bounce. Same base-path technique as Prelaunch::redirectToLanding so
        // /staging/... stays in /staging/.
        $host    = $_SERVER['HTTP_HOST'] ?? '';
        $scheme  = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ? 'https' : 'http';
        $scriptN = isset($_SERVER['SCRIPT_NAME']) ? $_SERVER['SCRIPT_NAME'] : '/';
        $base    = rtrim(str_replace('\\', '/', dirname($scriptN)), '/') . '/';
        header('Location: ' . $scheme . '://' . $host . $base . 'onboarding.php', true, 302);
        exit;
    }

    private static function currentScript()
    {
        global $p;
        if (isset($p) && is_string($p) && $p !== '') return basename($p);
        if (isset($_SERVER['SCRIPT_NAME']))            return basename($_SERVER['SCRIPT_NAME']);
        return '';
    }

    /** Expire Chameleon's persistent auto-login cookies. Without this, logout
     *  appears to succeed but the very next request reads c_user/c_password
     *  and re-authenticates the user, bouncing them back to /onboarding.php. */
    private static function clearRememberMeCookies()
    {
        if (headers_sent()) return;
        $past = time() - 3600;
        $host = $_SERVER['HTTP_HOST'] ?? '';
        // Strip the port if any
        if (strpos($host, ':') !== false) $host = explode(':', $host)[0];
        // Standard set + dot-prefix variant Chameleon uses on shared hosting
        foreach (array('c_user', 'c_password') as $base) {
            @setcookie($base, '', $past, '/');
            if ($host) {
                @setcookie($base, '', $past, '/', '.' . $host);
                @setcookie($base, '', $past, '/', $host);
            }
            unset($_COOKIE[$base]);
        }
    }
}
