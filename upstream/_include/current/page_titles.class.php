<?php
/* Per-page <title> and meta-description overrides.
 *
 * Hooked from Common::setSiteOptions().  For pages in our explicit map,
 * sets $g['main']['title'] and $g['main']['description'] so that
 * Common::parseSeoSite() (common.class.php:3638) takes its short-circuit
 * branch (the `if (isset($g['main']['description']))` test) and renders
 * those values into {title} and {description} on the page.
 *
 * Pages NOT in the map are left alone — parseSeoSite falls through to the
 * seo-DB lookup or its default config row, identical to behaviour before
 * this hook existed.  This is deliberate: dynamic title flows like
 * profile_view.php already build their own titles in the encoded core
 * (line 3689-3696), and overriding them globally would lose that.
 */

class PageTitles
{
    private static $defaultTitleSuffix = ' | Meet Greek Singles';

    /** [title, description] keyed by current script basename. */
    private static $map = array(
        'index.php' => array(
            'Meet Greek Singles | Serious Dating for the Greek Diaspora',
            'A calm, intentional dating community for Greeks worldwide and Philhellenes — find connections rooted in shared culture, values and identity.',
        ),
        'join.php' => array(
            'Create Your Free Account | Meet Greek Singles',
            'Join Meet Greek Singles in minutes. A serious, identity-rooted dating community for the Greek diaspora and Greeks in Greece.',
        ),
        'join2.php' => array(
            'Welcome | Meet Greek Singles',
            'You\'re almost in. A few details to start meeting Greek singles who share your values.',
        ),
        'join3.php' => array(
            'Welcome | Meet Greek Singles',
            'Welcome to Meet Greek Singles — your account is ready.',
        ),
        'about.php' => array(
            'About Us | Meet Greek Singles',
            'Why we built Meet Greek Singles — a calm, identity-rooted home for Greeks abroad and at home seeking meaningful connections.',
        ),
        'contact.php' => array(
            'Contact Us | Meet Greek Singles',
            'Get in touch with the Meet Greek Singles team — questions, partnerships, feedback all welcome.',
        ),
        'help.php' => array(
            'Questions & Answers | Meet Greek Singles',
            'Common questions about Meet Greek Singles answered.',
        ),
        'login.php' => array(
            'Log In | Meet Greek Singles',
            'Log in to your Meet Greek Singles account.',
        ),
        'forget_password.php' => array(
            'Reset Your Password | Meet Greek Singles',
            'Reset your Meet Greek Singles password and get back to your account.',
        ),
        'onboarding.php' => array(
            'Tell Us About You | Meet Greek Singles',
            'A few quick questions to help you find meaningful Greek connections.',
        ),
        'search_results.php' => array(
            'Find Greek Singles | Meet Greek Singles',
            'Search Greek singles by location, life stage and shared values across the diaspora.',
        ),
        'profile_settings.php' => array(
            'Profile Settings | Meet Greek Singles',
            'Update your account preferences, photos and visibility on Meet Greek Singles.',
        ),
        'subscriptions.php' => array(
            'Upgrade Your Membership | Meet Greek Singles',
            'Unlock the full Meet Greek Singles experience with a premium membership.',
        ),
        'pay.php' => array(
            'Upgrade Your Membership | Meet Greek Singles',
            'Upgrade to premium and unlock the full Meet Greek Singles experience.',
        ),
        'messages.php' => array(
            'Messages | Meet Greek Singles',
            'Your private messages with other Meet Greek Singles members.',
        ),
        'messages_one.php' => array(
            'Conversation | Meet Greek Singles',
            'Continue the conversation on Meet Greek Singles.',
        ),
        'events_index.php' => array(
            'Events | Meet Greek Singles',
            'Greek-hosted events and gatherings near you and online — discover community offline.',
        ),
        'events_calendar.php' => array(
            'Events Calendar | Meet Greek Singles',
            'Browse upcoming Greek events and meetups on Meet Greek Singles.',
        ),
        'events_my.php' => array(
            'My Events | Meet Greek Singles',
            'Events you\'re attending or have created on Meet Greek Singles.',
        ),
        'events_attending.php' => array(
            'Events I\'m Attending | Meet Greek Singles',
            'Greek events you\'ve said you\'re attending.',
        ),
        'events_event_show.php' => array(
            'Event | Meet Greek Singles',
            'Event details on Meet Greek Singles.',
        ),
        'events_create.php' => array(
            'Create an Event | Meet Greek Singles',
            'Host a Greek event or gathering and invite the community.',
        ),
        'email_not_confirmed.php' => array(
            'Confirm Your Email | Meet Greek Singles',
            'Please confirm your email to start using Meet Greek Singles.',
        ),
        'confirm_email.php' => array(
            'Email Confirmed | Meet Greek Singles',
            'Your email is confirmed — welcome to Meet Greek Singles.',
        ),
        'not_found.php' => array(
            'Page Not Found | Meet Greek Singles',
            'The page you were looking for could not be found.',
        ),
        'my_friends.php' => array(
            'My Connections | Meet Greek Singles',
            'Your connections and saved profiles on Meet Greek Singles.',
        ),
        'mutual_attractions.php' => array(
            'Mutual Attractions | Meet Greek Singles',
            'Members who liked you back — explore your mutual matches.',
        ),
    );

    /** URLs that route through router.php instead of mapping 1:1 to a PHP
     *  file in webroot. For these, $p resolves to whatever the encoded
     *  Router class includes (often unrelated to the user-visible URL),
     *  so we match on REQUEST_URI path instead. Checked BEFORE the script
     *  map so URI hits win when both could apply. */
    private static $uriMap = array(
        '/login'           => array(
            'Log In | Meet Greek Singles',
            'Log in to your Meet Greek Singles account.',
        ),
        '/forget_password' => array(
            'Reset Your Password | Meet Greek Singles',
            'Reset your Meet Greek Singles password and get back to your account.',
        ),
        '/forgot_password' => array(   // alternative spelling Chameleon also accepts
            'Reset Your Password | Meet Greek Singles',
            'Reset your Meet Greek Singles password and get back to your account.',
        ),
    );

    /** Invoked once per request from Common::setSiteOptions(). */
    public static function apply()
    {
        global $g;

        // 1) URI-path match first — handles router.php-routed URLs like /login
        $uri = isset($_SERVER['REQUEST_URI'])
             ? parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH)
             : null;
        if (is_string($uri) && $uri !== '') {
            $uri = '/' . trim($uri, '/');
            if (isset(self::$uriMap[$uri])) {
                self::set($g, self::$uriMap[$uri]);
                return;
            }
        }

        // 2) Script-basename match — covers normal /foo.php URLs
        $script = self::currentScript();
        if ($script === '') return;
        if (!isset(self::$map[$script])) return;
        self::set($g, self::$map[$script]);
    }

    /** Sets $g['main']['title'] + ['description']. parseSeoSite short-circuits
     *  on isset($g['main']['description']) (common.class.php:3642), not on
     *  title — so BOTH must be set or the SEO-DB lookup runs anyway. */
    private static function set(&$g, $entry)
    {
        list($title, $description) = $entry;
        if (!isset($g['main']) || !is_array($g['main'])) {
            $g['main'] = array();
        }
        $g['main']['title']       = $title;
        $g['main']['description'] = $description;
    }

    private static function currentScript()
    {
        global $p;
        if (isset($p) && is_string($p) && $p !== '') return basename($p);
        if (isset($_SERVER['SCRIPT_NAME'])) return basename($_SERVER['SCRIPT_NAME']);
        return '';
    }
}
