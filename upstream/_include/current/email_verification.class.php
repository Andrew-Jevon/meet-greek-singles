<?php
/* 2026-05-09 — email-verification gate.
 *
 * Hooked from Common::setSiteOptions() between Prelaunch and Onboarding.
 *
 * For logged-in users whose `user.active_code` is still non-empty (i.e. they
 * registered but haven't clicked the confirmation link in the email),
 * bounces every request that isn't part of the verification / auth / static
 * surface to /email_not_confirmed.php — where they can resend the link or
 * change the email address they registered with.
 *
 * Anonymous traffic isn't gated (Prelaunch handles that surface). Admin
 * users and admin-area paths are always allowed through.
 *
 * Chameleon already has a `join_unconfirmed_email_max_days` option, but it
 * deletes the account after the deadline rather than locking access while
 * the user is still in the grace window. Irene's brief is "fake-email
 * registrations must not get past registration", so we add the explicit
 * gate alongside the deletion job.
 */

class EmailVerification
{
    /** Scripts (basenames) that an unconfirmed user MAY visit without bouncing. */
    private static $allow = array(
        // The verification surface itself
        'email_not_confirmed.php',
        'confirm_email.php',
        // Auth + session lifecycle (so they can log out, reset password, or
        // resubmit the registration email if they fat-fingered it)
        'logout.php',
        'forget_password.php',
        // Registration flow — step 1 creates the user (logged-in + active_code
        // set), step 2 (/join2.php Done) submits the captcha and finishes the
        // profile. Without these in the allowlist, the gate fires on the step-2
        // AJAX and the JS spinner stalls until the user refreshes.
        'join.php',
        'join2.php',
        'join3.php',
        // Static + utility (CSS/JS/images/PWA — assets the verification page
        // itself needs to render)
        'ajax.php',
        'css.php', 'js.php',
        'tmpl_img_loader.php', 'files_uploader.php',
        'favicon.ico', 'robots.txt',
        'manifest.php',
        'serviceworker.js', 'sw.js',
        // Captcha (email_not_confirmed has a re-send form which may use it)
        'securimage_show_custom.php',
        'securimage_show.php',
        'securimage_audio.php',
        'securimage_play.php',
    );

    /** AJAX action names allowed even though ajax.php is in $allow. Keep tight. */
    private static $ajaxAllow = array(
        'check_mail_availability',
        'send_forgot_password',
        'confirm_email',
        'logout',
    );

    public static function apply()
    {
        // Never gate logout requests
        if (function_exists('get_param') && get_param('cmd') === 'logout') {
            return;
        }

        // setSiteOptions runs before $g_user is populated, so guid() can return 0.
        // Use Chameleon's session helper (the same one Prelaunch + Onboarding use).
        $uid = (int) (function_exists('get_session') ? get_session('user_id') : 0);
        if ($uid <= 0 && function_exists('guid')) $uid = (int) guid();
        if ($uid <= 0) return; // anonymous — Prelaunch handles them

        $row = DB::row("SELECT active_code, admin FROM user WHERE user_id = " . to_sql($uid, 'Number'));
        if (!$row) return;

        // Admin users always allowed
        if (!empty($row['admin'])) return;

        // Confirmed users (active_code cleared) — not gated
        if (empty($row['active_code'])) return;

        // Admin area never gated. Path check first because Common::isAdminSitePart()
        // has an internal allowlist that doesn't recognise admin pages we add
        // ourselves (e.g. M2 visibility_scope.php).
        if (strpos($_SERVER['SCRIPT_NAME'] ?? '', '/administration/') !== false) return;
        if (method_exists('Common', 'isAdminSitePart') && Common::isAdminSitePart()) return;

        $script = self::currentScript();
        if (in_array($script, self::$allow, true)) {
            // If it's ajax.php, also check the action name
            if ($script === 'ajax.php') {
                $action = get_param('action', '');
                if (!$action) $action = get_param('method', '');
                if ($action !== '' && !in_array($action, self::$ajaxAllow, true)) {
                    header('HTTP/1.1 403 Forbidden');
                    header('Content-Type: application/json; charset=utf-8');
                    echo json_encode(array(
                        'error'   => 'email_not_confirmed',
                        'message' => 'Please confirm your email address before using this feature.',
                    ));
                    exit;
                }
            }
            return;
        }

        // Bounce. Same base-path technique as Prelaunch::redirectToLanding so
        // /staging/... stays in /staging/.
        $host    = $_SERVER['HTTP_HOST'] ?? '';
        $scheme  = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ? 'https' : 'http';
        $scriptN = isset($_SERVER['SCRIPT_NAME']) ? $_SERVER['SCRIPT_NAME'] : '/';
        $base    = rtrim(str_replace('\\', '/', dirname($scriptN)), '/') . '/';
        header('Location: ' . $scheme . '://' . $host . $base . 'email_not_confirmed.php', true, 302);
        exit;
    }

    private static function currentScript()
    {
        global $p;
        if (isset($p) && is_string($p) && $p !== '') return basename($p);
        if (isset($_SERVER['SCRIPT_NAME']))            return basename($_SERVER['SCRIPT_NAME']);
        return '';
    }
}
