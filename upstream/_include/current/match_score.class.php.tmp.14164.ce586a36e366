<?php
/* Match score — 2026-05-04, per Irene's spec.
 *
 * Computes a 0–100 compatibility score between a viewer (the logged-in user)
 * and a candidate (any other user) using the four onboarding answers:
 *
 *     Q1  looking_for          (radio,    5 opts)  → 40 pts max
 *     Q2  culture_importance   (radio,    5 opts)  → 25 pts max
 *     Q3  greek_meaning        (checkbox, 6 opts)  → 20 pts max
 *     Q4  relocation_openness  (radio,    5 opts)  → 15 pts max
 *
 * Field-name mapping reference (added 2026-05-29) — admin_guide.md and the
 * older response drafts use descriptive English names; this is the technical
 * → descriptive map a future dev (or Irene reading the admin panel) needs:
 *
 *     looking_for          ↔ "Relationship intent" / "What are you looking for?"
 *     culture_importance   ↔ "Greek culture importance" / "How important is Greek culture in your life?"
 *     greek_meaning        ↔ "Shared values and traditions" / "What does being Greek mean to you?"
 *     relocation_openness  ↔ "Relocation openness" / "Do you see yourself open to relocating for the right person?"
 *
 * Note: "Connection to Greece" appears in older drafts as a 5th onboarding
 * question; it was moved OUT of onboarding during the final spec lock and is
 * now a profile-page field stored separately (not in this scorer).
 *
 * The hot path is `MatchScore::buildScoreSql($viewerUid)` — returns a SQL
 * fragment ready to drop into a SELECT, e.g.:
 *     SELECT u.user_id, …, ( <fragment> ) AS match_score FROM …
 * which lets `search_results.php` sort the result set by score in a single
 * query, no per-row PHP. Hooked from Users_List::show via $list->fieldsFromAdd
 * + $list->m_sql_order. See userslist.class.php.
 *
 * Why per-search rather than precomputed: for now the population is small
 * (pre-launch), the viewer's answers fit in a few ints, and there's no hot
 * dashboard demanding sub-50ms. If/when we have ~100k users and millions of
 * pair-scores would help, we can switch to a nightly batch-computed pivot
 * table — same field shapes, different storage.
 */

class MatchScore
{
    /* ── Adjacency / compatibility tables ────────────────────────────────────
     *
     * Format: $compat[$viewerOption][$candidateOption] = 0..1 multiplier of
     * the field's max points. Symmetric (compat[a][b] == compat[b][a]).
     *
     * Option IDs come from the var_<field> tables seeded by
     * _mgs_onboarding_refresh.php — they're 1-indexed AUTO_INCREMENTs in the
     * order Irene listed them (so e.g. var_looking_for.id=1 is "A meaningful,
     * long-term relationship"). 0 means the user hasn't answered.
     */

    // Q1 looking_for
    //  1 Long-term relationship   ┐
    //  2 Marriage                 │  cluster A — serious / forever
    //  3 Life partner             ┘
    //  4 Something serious, see where it leads      — flexible, leans serious
    //  5 Friendship first                            — different surface intent
    private static $lookingForCompat = array(
        1 => array(1=>1.00, 2=>1.00, 3=>1.00, 4=>0.70, 5=>0.10),
        2 => array(1=>1.00, 2=>1.00, 3=>1.00, 4=>0.65, 5=>0.05),
        3 => array(1=>1.00, 2=>1.00, 3=>1.00, 4=>0.70, 5=>0.10),
        4 => array(1=>0.70, 2=>0.65, 3=>0.70, 4=>1.00, 5=>0.45),
        5 => array(1=>0.10, 2=>0.05, 3=>0.10, 4=>0.45, 5=>1.00),
    );

    // Q4 relocation_openness
    //  1 Yes — anywhere
    //  2 Yes — within Greece
    //  3 Yes — abroad
    //  4 Maybe
    //  5 No — stay where I am
    private static $relocationCompat = array(
        1 => array(1=>1.00, 2=>0.75, 3=>0.75, 4=>0.70, 5=>0.20),
        2 => array(1=>0.75, 2=>1.00, 3=>0.50, 4=>0.55, 5=>0.40),
        3 => array(1=>0.75, 2=>0.50, 3=>1.00, 4=>0.55, 5=>0.20),
        4 => array(1=>0.70, 2=>0.55, 3=>0.55, 4=>1.00, 5=>0.55),
        5 => array(1=>0.20, 2=>0.40, 3=>0.20, 4=>0.55, 5=>1.00),
    );

    // Per-field max points (sum to 100, exactly Irene's weights)
    const PTS_LOOKING_FOR        = 40;
    const PTS_CULTURE_IMPORTANCE = 25;
    const PTS_GREEK_MEANING      = 20;
    const PTS_RELOCATION         = 15;

    // Bits available for greek_meaning (6 options → 6 bits)
    const GREEK_MEANING_BITS     = 6;

    // ── Public API ──────────────────────────────────────────────────────────

    /** True if the user has enough onboarding answers to compute a meaningful
     *  score. We require all four to avoid skewed comparisons. */
    public static function userHasAnswers($uid)
    {
        $uid = (int) $uid;
        if ($uid <= 0) return false;
        $row = DB::row("SELECT looking_for, culture_importance, greek_meaning, relocation_openness
                          FROM userinfo WHERE user_id = $uid");
        if (!$row) return false;
        return !empty($row['looking_for'])
            && !empty($row['culture_importance'])
            && !empty($row['greek_meaning'])
            && !empty($row['relocation_openness']);
    }

    /** Compute a 0–100 score between two users. Used for ad-hoc PHP-side
     *  comparisons (e.g. "Why did this person rank above that one?"). */
    public static function compute($viewerUid, $candidateUid)
    {
        $viewerUid    = (int) $viewerUid;
        $candidateUid = (int) $candidateUid;
        if ($viewerUid <= 0 || $candidateUid <= 0) return 0;

        $a = DB::row("SELECT looking_for, culture_importance, greek_meaning, relocation_openness
                        FROM userinfo WHERE user_id = $viewerUid");
        $b = DB::row("SELECT looking_for, culture_importance, greek_meaning, relocation_openness
                        FROM userinfo WHERE user_id = $candidateUid");
        if (!$a || !$b) return 0;

        return (int) round(
            self::scoreLookingFor((int) $a['looking_for'], (int) $b['looking_for'])
          + self::scoreCultureImportance((int) $a['culture_importance'], (int) $b['culture_importance'])
          + self::scoreGreekMeaning((int) $a['greek_meaning'], (int) $b['greek_meaning'])
          + self::scoreRelocation((int) $a['relocation_openness'], (int) $b['relocation_openness'])
        );
    }

    /** Build a SQL expression that evaluates to the candidate's match_score
     *  against $viewerUid, ready to drop into a SELECT. Returns empty string
     *  if the viewer hasn't answered onboarding (caller should skip injection
     *  in that case). The candidate row is expected to be aliased as `i`
     *  (userinfo) — the alias Users_List uses internally. */
    public static function buildScoreSql($viewerUid)
    {
        $viewerUid = (int) $viewerUid;
        if ($viewerUid <= 0) return '';
        $v = DB::row("SELECT looking_for, culture_importance, greek_meaning, relocation_openness
                        FROM userinfo WHERE user_id = $viewerUid");
        if (!$v) return '';
        $vL = (int) $v['looking_for'];
        $vC = (int) $v['culture_importance'];
        $vG = (int) $v['greek_meaning'];
        $vR = (int) $v['relocation_openness'];
        if (!$vL || !$vC || !$vG || !$vR) return '';

        $partLooking    = self::sqlCaseFromCompat('i.looking_for',         $vL, self::$lookingForCompat,  self::PTS_LOOKING_FOR);
        $partCulture    = self::sqlCultureImportance('i.culture_importance', $vC);
        $partGreek      = self::sqlGreekMeaning('i.greek_meaning', $vG);
        $partRelocation = self::sqlCaseFromCompat('i.relocation_openness', $vR, self::$relocationCompat, self::PTS_RELOCATION);

        // Wrap the whole thing in COALESCE so missing-userinfo rows don't NULL.
        return "COALESCE(($partLooking) + ($partCulture) + ($partGreek) + ($partRelocation), 0)";
    }

    // ── PHP-side scoring (mirrors the SQL exactly) ───────────────────────────

    private static function scoreLookingFor($a, $b)
    {
        if (!$a || !$b) return 0;
        $m = isset(self::$lookingForCompat[$a][$b]) ? self::$lookingForCompat[$a][$b] : 0;
        return $m * self::PTS_LOOKING_FOR;
    }

    private static function scoreCultureImportance($a, $b)
    {
        if (!$a || !$b) return 0;
        $diff = abs($a - $b);
        $mult = ($diff === 0) ? 1.00
              : (($diff === 1) ? 0.72
              : (($diff === 2) ? 0.44
              : (($diff === 3) ? 0.20 : 0.00)));
        return $mult * self::PTS_CULTURE_IMPORTANCE;
    }

    private static function scoreGreekMeaning($aMask, $bMask)
    {
        if (!$aMask || !$bMask) return 0;
        $intersect = self::popcount($aMask & $bMask);
        $bitsViewer = self::popcount($aMask);
        if ($bitsViewer === 0) return 0;
        return ($intersect / $bitsViewer) * self::PTS_GREEK_MEANING;
    }

    private static function scoreRelocation($a, $b)
    {
        if (!$a || !$b) return 0;
        $m = isset(self::$relocationCompat[$a][$b]) ? self::$relocationCompat[$a][$b] : 0;
        return $m * self::PTS_RELOCATION;
    }

    private static function popcount($n)
    {
        $n = (int) $n;
        $c = 0;
        while ($n > 0) { $c += ($n & 1); $n >>= 1; }
        return $c;
    }

    // ── SQL builders ────────────────────────────────────────────────────────

    /** Build a CASE expression that maps each candidate option ID to (compat
     *  multiplier × max points). The viewer's option is a fixed PHP int, so
     *  we look up self::$compat[$viewerOpt] once here. */
    private static function sqlCaseFromCompat($col, $viewerOpt, $compat, $maxPts)
    {
        $branches = array();
        if (!isset($compat[$viewerOpt])) {
            // Viewer has an unknown option — score everyone 0 for this field.
            return "0";
        }
        foreach ($compat[$viewerOpt] as $candidateOpt => $mult) {
            $pts = round($mult * $maxPts, 2);
            $branches[] = "WHEN $col = " . (int) $candidateOpt . " THEN $pts";
        }
        return "CASE " . implode(' ', $branches) . " ELSE 0 END";
    }

    /** Linear scale (1..5). Max at exact match, fades by 1 step.
     *  Mirrors scoreCultureImportance(). */
    private static function sqlCultureImportance($col, $viewerOpt)
    {
        $vO = (int) $viewerOpt;
        $p1 = self::PTS_CULTURE_IMPORTANCE;            // exact
        $p2 = round($p1 * 0.72, 2);                    // 1 step
        $p3 = round($p1 * 0.44, 2);                    // 2 steps
        $p4 = round($p1 * 0.20, 2);                    // 3 steps
        return "CASE WHEN $col = 0 THEN 0
                     WHEN $col = $vO THEN $p1
                     WHEN ABS($col - $vO) = 1 THEN $p2
                     WHEN ABS($col - $vO) = 2 THEN $p3
                     WHEN ABS($col - $vO) = 3 THEN $p4
                     ELSE 0 END";
    }

    /** Bitmask intersection / viewer's bit count × max pts.
     *  MySQL's BIT_COUNT() does the popcount for us. */
    private static function sqlGreekMeaning($col, $viewerMask)
    {
        $vM = (int) $viewerMask;
        $vBits = self::popcount($vM);
        if ($vBits === 0) return "0";
        $maxPts = self::PTS_GREEK_MEANING;
        return "(BIT_COUNT($col & $vM) / $vBits) * $maxPts";
    }
}
