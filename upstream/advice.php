<?php
/* 2026-06-09 (Q25 per Irene) — Advice page.
 *
 * Mirrors the about.php pattern: pulls page content from the `pages` table
 * by the menu_title alias `menu_top_advice` (inserted in advice_page_insert.sql).
 * Admin can edit the final wording when Irene sends Q26 content via the
 * standard Page Editor in /administration/pages.php.
 */

include("./_include/core/main_start.php");

class CAdvice extends CHtmlBlock
{
    function parseBlock(&$html)
    {
        $pageId = CustomPage::getIdFromAlias('menu_top_advice');
        CustomPage::parsePage($html, $pageId);

        TemplateEdge::parseColumn($html);

        parent::parseBlock($html);
    }
}

$page = new CAdvice("", getPageCustomTemplate('about.html', 'custom_page_template'));
$header = new CHeader("header", $g['tmpl']['dir_tmpl_main'] . "_header.html");
$page->add($header);

$footer = new CFooter("footer", $g['tmpl']['dir_tmpl_main'] . "_footer.html");
$page->add($footer);

include("./_include/core/main_close.php");
