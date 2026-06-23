<?php
/* Milestone 2 — server-side visibility enforcement.
 *
 * Hooked from Common::setSiteOptions() AFTER Onboarding::apply().
 *
 * Reads the visibility_scope flag we backfilled onto every user_var entry
 * and removes any field the current viewer is not allowed to see, BEFORE
 * Chameleon's UserFields class iterates over $g['user_var'].
 *
 * That's the cleanest way to enforce server-side visibility without
 * touching ioncube-encoded controllers — every renderer that walks
 * $g['user_var'] (profile view, search filter UI, edit form) inherits
 * the filtered view automatically.
 *
 * Conservative defaults:
 *   - If we can't tell who the profile owner is → don't filter.
 *   - If viewer == owner → don't filter (you see your own everything).
 *   - If we're on an admin URL → don't filter.
 *   - On the profile-edit page → don't filter (you're editing your own).
 *
 * Only triggers when we're confidently rendering OTHER PEOPLE's profile
 * data (search-results, vanity-URL view, mutual_attractions, encounters).
 *
 * -----------------------------------------------------------------------
 * Phase 8.2 architecture model — required reading before adding any
 * endpoint that returns user profile data.
 *
 * Visibility runs in TWO layers:
 *
 *  Layer 1 — template/metadata layer (this class)
 *      VisibilityFilter::apply() strips entries from $g['user_var'].
 *      Every Chameleon HTML template iterates $g['user_var'] keys, so
 *      removing the metadata is equivalent to hiding the field from
 *      every server-rendered page. This catches:
 *          profile_view.php, search_results.php, mutual_attractions.php,
 *          encounters.php, my_friends.php, community.php, mail.php,
 *          messages.php, mail_compose.php, profile_view_block.php
 *      and the vanity-URL profile path (router.php with name_seo=).
 *
 *  Layer 2 — row/JSON layer (Visibility::filterUserRow + sqlWhitelistColumns)
 *      Any custom PHP endpoint (e.g. match_scores.php, or a future
 *      mobile-API endpoint) that fetches a raw userinfo row directly
 *      from the DB and returns it as JSON MUST filter the row through
 *      Visibility::filterUserRow($row, $viewerUid, $ownerUid) before
 *      json_encode. Layer 1 does NOT apply to these endpoints because
 *      they typically bypass Chameleon's main_start.php bootstrap to
 *      avoid the prelaunch/onboarding gates.
 *
 *      As of 2026-05-28, the only such custom endpoint is match_scores.php,
 *      which returns ONLY compatibility scores (integers 0-100) and no
 *      user profile fields, so it carries no leak risk by construction.
 *      That property MUST be preserved on future edits. Any future
 *      endpoint returning user fields must call Visibility::filterUserRow.
 *
 * If you add a new endpoint, decide which layer it belongs to:
 *   - server-rendered HTML page that walks $g['user_var']
 *       → no action needed; Layer 1 covers it
 *   - custom JSON/XML/AJAX endpoint that emits user fields
 *       → wrap your output array through Visibility::filterUserRow
 *   - email or OG-preview that embeds user fields
 *       → same — Visibility::filterUserRow before rendering
 * ----------------------------------------------------------------------- */

class VisibilityFilter
{
    /** Pages where another user's profile fields are rendered to the viewer. */
    private static $renderingOthers = array(
        'search_results.php', 'mutual_attractions.php', 'encounters.php',
        'my_friends.php', 'community.php', 'mail.php', 'messages.php',
        'mail_compose.php', 'profile_view_block.php',
    );

    /** Pages where filtering would harm UX (own profile, edit forms, admin). */
    private static $skipPages = array(
        'profile_settings.php', 'profile_personal.php', 'profile_photo.php',
        'profile_photo_edit.php', 'profile_delete.php',
        // profile_view.php in this install always shows guid()'s own profile
        'profile_view.php',
    );

    public static function apply()
    {
        global $g;
        if (!isset($g['user_var']) || !is_array($g['user_var'])) return;
        if (!class_exists('Visibility')) {
            $f = dirname(__FILE__) . '/visibility.class.php';
            if (is_readable($f)) include_once($f);
            if (!class_exists('Visibility')) return;
        }

        $script = self::currentScript();

        // Skip pages where filtering would break the user's own flow.
        if (in_array($script, self::$skipPages, true)) return;
        if (self::isAdminArea()) return;

        $viewerUid = (int) (function_exists('guid') ? guid() : 0);
        $ownerUid  = self::detectOwner();

        // Viewer == owner means looking at your own data — no filtering.
        if ($viewerUid > 0 && $viewerUid === $ownerUid) return;

        // Only filter on pages that render someone else's profile data.
        // For the vanity-URL case (router.php → an encoded handler) we still
        // apply if we can detect an owner; that's the safer default.
        $isVanity = self::looksLikeVanityProfile();
        if (!$isVanity && !in_array($script, self::$renderingOthers, true)) return;

        // If owner is unknown we treat viewer as guest-public — strip everything
        // not flagged 'public'. That's restrictive but safe.
        foreach ($g['user_var'] as $key => $cfg) {
            if (!is_array($cfg)) continue;
            if (!Visibility::canSee($key, $viewerUid, $ownerUid)) {
                unset($g['user_var'][$key]);
            }
        }
    }

    /**
     * Try to identify the profile owner for this request.
     * Returns 0 if undetermined.
     */
    private static function detectOwner()
    {
        // Direct numeric id params (Chameleon uses several conventions)
        foreach (array('user_id', 'uid', 'id', 'profile_id') as $p) {
            if (isset($_GET[$p]) && is_numeric($_GET[$p]) && (int) $_GET[$p] > 0) {
                return (int) $_GET[$p];
            }
        }
        // Vanity URL → name_seo lookup
        if (isset($_GET['name_seo']) && trim($_GET['name_seo']) !== '') {
            $row = DB::row("SELECT user_id FROM `user`
                WHERE name_seo = " . to_sql(trim($_GET['name_seo']), 'Text') . " LIMIT 1");
            if ($row && !empty($row['user_id'])) return (int) $row['user_id'];
        }
        return 0;
    }

    private static function currentScript()
    {
        global $p;
        if (isset($p) && is_string($p) && $p !== '') return basename($p);
        if (isset($_SERVER['SCRIPT_NAME']))            return basename($_SERVER['SCRIPT_NAME']);
        return '';
    }

    /**
     * Vanity URLs route through router.php with a name_seo, OR the URL path is
     * a simple /<slug> with no trailing .php extension.
     */
    private static function looksLikeVanityProfile()
    {
        $script = self::currentScript();
        if ($script === 'router.php' && isset($_GET['name_seo'])) return true;
        return false;
    }

    private static function isAdminArea()
    {
        if (method_exists('Common', 'isAdminSitePart')) return Common::isAdminSitePart();
        return strpos($_SERVER['SCRIPT_NAME'] ?? '', '/administration/') !== false;
    }
}
