<?php
/*
 * 2026-06-05 (Milestone B) — Cloudflare Turnstile server-side verification.
 *
 * Frontend renders Turnstile widgets on /register and /login (see the
 * <script src="...turnstile/v0/api.js"...> loader at the top of each
 * template and the <div class="cf-turnstile" data-sitekey="..."> markup
 * near the submit buttons). The widget injects the token into the form
 * as the field `cf-turnstile-response`.
 *
 * This file provides the server-side check. Call TurnstileVerify::check()
 * from the registration and login handlers BEFORE creating the account
 * or authenticating the user. A failed check should reject the request
 * with the same "incorrect captcha" error path the old securimage CAPTCHA
 * used to take.
 *
 * Wire-up checklist for production:
 *
 *   1. In dash.cloudflare.com → Turnstile, create a widget for
 *      meetgreeksingles.com. Cloudflare returns a Site Key (public, goes
 *      in the HTML) and a Secret Key (private, goes here on the server).
 *
 *   2. Replace the placeholder Site Key `1x00000000000000000000AA` in the
 *      following templates with the real Site Key:
 *        - _frameworks/main/impact/register.html
 *        - _frameworks/main/impact/login.html
 *
 *   3. Set the Secret Key below by either:
 *      a. defining the constant TURNSTILE_SECRET_KEY in a server-only
 *         config file that is NOT committed to the project, or
 *      b. setting it as an environment variable TURNSTILE_SECRET and
 *         reading it via getenv() below.
 *
 *   4. In the registration handler (the code path that runs when the
 *      /register form is submitted) and the login handler (ajax.php
 *      cmd=login), add:
 *
 *          require_once dirname(__FILE__) . '/_include/current/turnstile_verify.php';
 *          if (!TurnstileVerify::check()) {
 *              // reject — same error path as the old captcha failure
 *              return ['error' => 'incorrect_captcha'];
 *          }
 *
 *   5. Remove the securimage_show_custom.php inclusion from join2.html
 *      (or leave it as a fallback during a brief transition window).
 *
 * Test keys for development (always pass / always fail):
 *   Always-passes site key: 1x00000000000000000000AA
 *   Always-passes secret:   1x0000000000000000000000000000000AA
 *   Always-fails  site key: 2x00000000000000000000AB
 *   Always-fails  secret:   2x0000000000000000000000000000000AA
 *
 * Reference: https://developers.cloudflare.com/turnstile/get-started/server-side-validation/
 */

class TurnstileVerify
{
    const VERIFY_URL = 'https://challenges.cloudflare.com/turnstile/v0/siteverify';

    /**
     * Returns true if the Turnstile token in the current request is valid,
     * false if it is missing, malformed, or rejected by Cloudflare.
     * Safe to call from both POST forms (register) and AJAX (login).
     */
    public static function check()
    {
        $token = isset($_POST['cf-turnstile-response']) ? $_POST['cf-turnstile-response'] : '';
        if ($token === '') return false;

        $secret = self::secretKey();
        if ($secret === '') {
            // No secret configured yet. During the wiring transition, fail
            // CLOSED — don't accept any submission, so we never silently
            // skip the gate. To temporarily disable, return true here.
            return false;
        }

        $payload = http_build_query(array(
            'secret'   => $secret,
            'response' => $token,
            'remoteip' => self::clientIp(),
        ));

        // Prefer cURL (most hosts have it), fall back to file_get_contents
        // with a stream context if cURL is unavailable.
        if (function_exists('curl_init')) {
            $ch = curl_init(self::VERIFY_URL);
            curl_setopt_array($ch, array(
                CURLOPT_POST           => true,
                CURLOPT_POSTFIELDS     => $payload,
                CURLOPT_RETURNTRANSFER => true,
                CURLOPT_TIMEOUT        => 5,
                CURLOPT_CONNECTTIMEOUT => 3,
                CURLOPT_SSL_VERIFYPEER => true,
            ));
            $resp = curl_exec($ch);
            curl_close($ch);
        } else {
            $ctx = stream_context_create(array('http' => array(
                'method'        => 'POST',
                'header'        => "Content-Type: application/x-www-form-urlencoded\r\n",
                'content'       => $payload,
                'timeout'       => 5,
                'ignore_errors' => true,
            )));
            $resp = @file_get_contents(self::VERIFY_URL, false, $ctx);
        }

        if (!$resp) return false;
        $data = json_decode($resp, true);
        return is_array($data) && !empty($data['success']);
    }

    private static function secretKey()
    {
        if (defined('TURNSTILE_SECRET_KEY') && TURNSTILE_SECRET_KEY) {
            return TURNSTILE_SECRET_KEY;
        }
        $env = getenv('TURNSTILE_SECRET');
        return $env !== false ? $env : '';
    }

    private static function clientIp()
    {
        foreach (array('HTTP_CF_CONNECTING_IP', 'HTTP_X_FORWARDED_FOR', 'REMOTE_ADDR') as $h) {
            if (!empty($_SERVER[$h])) {
                $ip = trim(explode(',', $_SERVER[$h])[0]);
                if (filter_var($ip, FILTER_VALIDATE_IP)) return $ip;
            }
        }
        return '';
    }
}
