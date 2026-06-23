<?php
/* Milestone 2 — server-side visibility helper.
 *
 * Reads the `visibility_scope` flag we backfilled onto every user_var entry
 * (M3 installer 2026-04-25). Tells callers whether a given profile field
 * should be shown to a given viewer.
 *
 * Use:
 *   if (Visibility::canSee($fieldKey, $viewerUid, $ownerUid)) { ... }
 *
 * Scopes:
 *   public  — anyone (incl. logged-out)
 *   member  — any logged-in user
 *   owner   — only the field owner themselves
 *
 * Default (no flag set): 'member' — same as Chameleon's pre-M2 behaviour.
 */

class Visibility
{
    public static function scopeOf($fieldKey)
    {
        global $g;
        if (!isset($g['user_var'][$fieldKey])) return 'member';
        $cfg = $g['user_var'][$fieldKey];
        if (!is_array($cfg)) return 'member';
        return isset($cfg['visibility_scope']) ? $cfg['visibility_scope'] : 'member';
    }

    public static function canSee($fieldKey, $viewerUid, $ownerUid)
    {
        $scope    = self::scopeOf($fieldKey);
        $viewerUid = (int) $viewerUid;
        $ownerUid  = (int) $ownerUid;

        switch ($scope) {
            case 'public':  return true;
            case 'owner':   return ($viewerUid > 0 && $viewerUid === $ownerUid);
            case 'member':
            default:        return ($viewerUid > 0);
        }
    }

    /** Filter a userinfo-style assoc array down to fields the viewer is allowed to see. */
    public static function filter(array $row, $viewerUid, $ownerUid)
    {
        $out = array();
        foreach ($row as $k => $v) {
            if (self::canSee($k, $viewerUid, $ownerUid)) {
                $out[$k] = $v;
            }
        }
        return $out;
    }

    /** Convenience: list of field keys filtered by scope, useful for templates. */
    public static function visibleFields($viewerUid, $ownerUid)
    {
        global $g;
        $out = array();
        if (!isset($g['user_var']) || !is_array($g['user_var'])) return $out;
        foreach ($g['user_var'] as $k => $cfg) {
            if (!is_array($cfg)) continue;
            if (self::canSee($k, $viewerUid, $ownerUid)) $out[] = $k;
        }
        return $out;
    }

    /**
     * Phase 8.2 — column allowlist for raw SQL SELECT / JSON endpoints.
     *
     * Returns the subset of $g['user_var'] keys this viewer is allowed to
     * see on this owner's record. Custom endpoints that bypass the
     * template layer (AJAX returning JSON, mobile API, OG previews,
     * email notifications) should call this BEFORE serializing user
     * data, so a guest can't fetch member/owner-scoped fields via a
     * crafted request.
     *
     * Typical use in a JSON endpoint:
     *   $allowed = Visibility::sqlWhitelistColumns($viewerUid, $ownerUid);
     *   $row = DB::row("SELECT user_id, " . implode(',', array_map('to_sql_col', $allowed)) . " FROM userinfo WHERE user_id = ...");
     *   echo json_encode($row);
     *
     * Or, when the row is already in memory:
     *   $safe = Visibility::filterUserRow($row, $viewerUid, $ownerUid);
     *
     * Returns a numerically-indexed array of column names.
     */
    public static function sqlWhitelistColumns($viewerUid, $ownerUid)
    {
        return self::visibleFields($viewerUid, $ownerUid);
    }

    /**
     * Phase 8.2 — filter an associative row (already fetched from DB or
     * in-memory) down to the columns this viewer may see. Identical to
     * filter() but named for the common case (sanitizing a userinfo row
     * before json_encode). Always-non-user_var columns (e.g. user_id,
     * name, name_seo, online) are preserved — those are public-by-design
     * identifiers, not user-controlled profile fields.
     */
    public static function filterUserRow(array $row, $viewerUid, $ownerUid)
    {
        global $g;
        if (!isset($g['user_var']) || !is_array($g['user_var'])) return $row;
        $out = array();
        foreach ($row as $k => $v) {
            // Keys not in user_var are framework/identity columns — always allow.
            if (!isset($g['user_var'][$k])) { $out[$k] = $v; continue; }
            if (self::canSee($k, $viewerUid, $ownerUid)) {
                $out[$k] = $v;
            }
        }
        return $out;
    }
}
