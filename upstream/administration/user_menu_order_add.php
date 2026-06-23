<?php
/* (C) Websplosion LLC, 2001-2021

IMPORTANT: This is a commercial software product
and any kind of using it must agree to the Websplosion's license agreement.
It can be found at http://www.chameleonsocial.com/license.doc

This notice may not be removed from the source code. */

include("../_include/core/administration_start.php");

class CCustomPageAdd extends CHtmlBlock {

    private $table = 'col_order';

    function action()
    {
        global $p;

        $cmd = get_param('cmd');

        if ($cmd == 'save') {
            $maxPosition = DB::result("SELECT MAX(position) FROM `" . $this->table . "` WHERE `lang` = 'default'");
            $data = array(
                'name' => trim(get_param('name')),
                'title' => trim(get_param('title')),
                'content' => trim(get_param('content')),
                'section' => trim(get_param('section')),
                'position' => $maxPosition + 1,
                'lang' => 'default',
            );
            DB::insert($this->table, $data);
            redirect('user_menu_order.php?action=saved');
        }
    }

    function parseBlock(&$html)
    {
        global $g;

        $lang = Common::getOption('administration', 'lang_value');
        $langTinymceUrl =  $g['tmpl']['url_tmpl_administration'] . "js/tinymce/langs/{$lang}.js";
        if (!file_exists($langTinymceUrl)) {
            $lang = 'default';
        }
        $html->setvar('lang_vw', $lang);

        $html->parse('block_menu');

        $html->setvar('page_section', 'mobile_user_menu' . CustomPage::getMenuNamePostfix());

        $html->setvar('page_key', 'name');
        $html->parse('content');

		if (isset(CAdminHeader::$linkToMainMenuAdmin['user_menu_order'])) {
			$html->setvar('section_page',  CAdminHeader::$linkToMainMenuAdmin['user_menu_order']);
		}

        parent::parseBlock($html);
    }

}

$page = new CCustomPageAdd("", $g['tmpl']['dir_tmpl_administration'] . "user_menu_order_edit.html");

$header = new CAdminHeader("header", $g['tmpl']['dir_tmpl_administration'] . "_header.html");
$page->add($header);
$footer = new CAdminFooter("footer", $g['tmpl']['dir_tmpl_administration'] . "_footer.html");
$page->add($footer);

$page->add(new CAdminPageMenuOptions());

include("../_include/core/administration_close.php");