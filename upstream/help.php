<?php
/* (C) Websplosion LLC, 2001-2021

IMPORTANT: This is a commercial software product
and any kind of using it must agree to the Websplosion's license agreement.
It can be found at http://www.chameleonsocial.com/license.doc

This notice may not be removed from the source code. */

$area = "public";
include("./_include/core/main_start.php");
if(!Common::isOptionActive('help')) {
    redirect(Common::toHomePage());
}
class CHelp extends CHtmlBlock
{

	var $message;

	function parseBlock(&$html)
	{

        $lang = Common::getOption('lang_loaded', 'main');
        $isMember = guid();

        // Refinement: order by `position` if the column exists, falling back to id.
        $hasPosition = DB::result("SELECT COUNT(*) FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name   = 'help_topic'
              AND column_name  = 'position'");
        $orderBy = $hasPosition ? 'position ASC, id ASC' : 'id ASC';

        $hasPublicFlag = DB::result("SELECT COUNT(*) FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name   = 'help_topic'
              AND column_name  = 'public_visible'");

        if (!$isMember) {
            // Guest path: top public topics only, names only, with Join CTA.
            $url = Common::pageUrl('join');
            $html->setvar('url_page_join', $url);

            $publicWhere = $hasPublicFlag ? ' AND public_visible = 1 ' : '';
            $sql = 'SELECT id, name FROM help_topic
                WHERE lang = ' . to_sql($lang) . $publicWhere . '
                ORDER BY ' . $orderBy . ' LIMIT 8';
            DB::query($sql);
            while ($row = DB::fetch_row()) {
                $html->setvar('id', $row['id']);
                $html->setvar('name', $row['name']);
                $html->parse('public_question', true);
            }
            $html->parse('guest_view', false);

            parent::parseBlock($html);
            return;
        }

        // Member path: full Q&A as before.
        $sql = 'SELECT id, name FROM help_topic
            WHERE lang = ' . to_sql($lang) . '
            ORDER BY ' . $orderBy;
		DB::query($sql);
		$i = 1;
		while ($row = DB::fetch_row())
		{
			$html->setvar("id", $row['id']);
			$html->setvar("name", $row['name']);
			if ($i % 3 == 0)
			{
				$html->parse("topic_column", false);
			}
			else
			{
				$html->setblockvar("topic_column", "");
			}
			$html->parse("topic", true);
			$i++;
		}

		$t = get_param('t', 0);
		$topic = DB::row("SELECT * FROM help_topic WHERE id=" . to_sql($t, "Number") . "");
        if($topic) {
            if($topic['lang'] != $lang) {
                redirect('help.php');
            }
            $html->setvar('topic_name', $topic['name']);
        }

		DB::query("SELECT id, name, text FROM help_answer WHERE topic_id=" . to_sql($t, "Number") . " ORDER BY id");
        $parse = false;
		while ($row = DB::fetch_row())
		{
			$html->setvar("id", $row['id']);
			$html->setvar("name", $row['name']);
			$html->setvar("text", nl2br($row['text']));

			$html->parse("show", true);
			$html->parse("hide", true);
			$html->parse("question", true);
            $parse = true;
		}

        if($parse) {
            $html->parse('show_hide');
        }

        $html->parse('member_view', false);

		parent::parseBlock($html);
	}
}

$page = new CHelp("", $g['tmpl']['dir_tmpl_main'] . "help.html");
$header = new CHeader("header", $g['tmpl']['dir_tmpl_main'] . "_header.html");
$page->add($header);
$footer = new CFooter("footer", $g['tmpl']['dir_tmpl_main'] . "_footer.html");
$page->add($footer);

include("./_include/core/main_close.php");

?>
