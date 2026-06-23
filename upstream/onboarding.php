<?php
/* Milestone 3 — post-registration onboarding flow.
 *
 * Reads $g['user_var'] for any field flagged is_onboarding=1 and renders them
 * in user_var position order as a 4-card flow. On submit, writes answers
 * into userinfo.<field> and sets user.onboarding_done = 1.
 *
 * Logged-in users only. If onboarding_done = 1 already, redirects home.
 */

include("./_include/core/main_start.php");

if (!guid()) {
    redirect(Common::pageUrl('login'));
}

class COnboarding extends CHtmlBlock
{
    function action()
    {
        global $g, $g_user;

        $cmd = get_param('cmd');
        if ($cmd !== 'submit') return;

        $uid = (int) $g_user['user_id'];
        if ($uid <= 0) return;

        $sets = array();
        foreach ($g['user_var'] as $key => $cfg) {
            if (!is_array($cfg) || empty($cfg['is_onboarding'])) continue;
            $val = get_param($key, null);
            if ($cfg['type'] === 'checkbox') {
                if (is_array($val)) {
                    $bits = 0;
                    foreach ($val as $optId) {
                        $optId = (int) $optId;
                        if ($optId > 0 && $optId < 64) {
                            $bits |= (1 << ($optId - 1));
                        }
                    }
                    $sets[] = "`$key` = " . to_sql($bits, 'Number');
                } else {
                    $sets[] = "`$key` = 0";
                }
            } else {
                $sets[] = "`$key` = " . to_sql((int) $val, 'Number');
            }
        }

        if (!empty($sets)) {
            DB::execute("UPDATE userinfo SET " . implode(', ', $sets) .
                        " WHERE user_id = " . to_sql($uid, 'Number'));
        }
        DB::execute("UPDATE user SET onboarding_done = 1 WHERE user_id = " .
                    to_sql($uid, 'Number'));

        redirect(Common::getHomePage());
    }

    function parseBlock(&$html)
    {
        global $g, $g_user;

        $uid = (int) $g_user['user_id'];

        // Already done? Skip.
        $done = DB::result("SELECT onboarding_done FROM user WHERE user_id = " .
                           to_sql($uid, 'Number'));
        if ((int) $done === 1) {
            redirect(Common::getHomePage());
        }

        // Collect onboarding fields from $g['user_var']
        $onboardingFields = array();
        foreach ($g['user_var'] as $key => $cfg) {
            if (is_array($cfg) && !empty($cfg['is_onboarding'])) {
                $onboardingFields[$key] = $cfg;
            }
        }
        $total = count($onboardingFields);

        $i = 0;
        foreach ($onboardingFields as $key => $cfg) {
            $i++;

            // CRITICAL: Chameleon's parser accumulates parsed sub-blocks across
            // iterations of the parent block. Without clean() here, the options
            // rendered for card N would also appear inside cards N+1, N+2, etc.
            // Reported by Irene 2026-05-04 as "previous answers showing on each
            // next question" / "same answer options appearing across multiple
            // questions" — bug had been latent since M3 (2026-04-25).
            $html->clean('opt_radio');
            $html->clean('opt_checkbox');
            $html->clean('subtitle');

            $html->setvar('q_index',  $i);
            $html->setvar('q_total',  $total);
            $html->setvar('q_name',   $key);
            $html->setvar('q_title',  htmlspecialchars($cfg['title'], ENT_QUOTES, 'UTF-8'));
            $html->setvar('q_type',   $cfg['type']);
            $html->setvar('q_input_name', $cfg['type'] === 'checkbox' ? "{$key}[]" : $key);
            $html->setvar('card_active', $i === 1 ? 'is-active' : '');

            if (!empty($cfg['subtitle'])) {
                $html->setvar('q_subtitle', htmlspecialchars($cfg['subtitle'], ENT_QUOTES, 'UTF-8'));
                $html->parse('subtitle', false);
            }

            // Pull options from var_<field> table
            DB::query("SELECT id, title FROM `{$cfg['table']}` ORDER BY id");
            while ($opt = DB::fetch_row()) {
                $html->setvar('opt_id',    (int) $opt['id']);
                $html->setvar('opt_title', htmlspecialchars($opt['title'], ENT_QUOTES, 'UTF-8'));
                if ($cfg['type'] === 'checkbox') {
                    $html->parse('opt_checkbox', true);
                } else {
                    $html->parse('opt_radio', true);
                }
            }

            $html->parse('card', true);
        }

        parent::parseBlock($html);
    }
}

$page = new COnboarding("", $g['tmpl']['dir_tmpl_main'] . "onboarding.html");
$page->action();

$header = new CHeader("header", $g['tmpl']['dir_tmpl_main'] . "_header.html");
$page->add($header);
$footer = new CFooter("footer", $g['tmpl']['dir_tmpl_main'] . "_footer.html");
$page->add($footer);

include("./_include/core/main_close.php");
