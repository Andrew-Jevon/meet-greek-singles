<?php
/* (C) Websplosion LLC, 2001-2021

IMPORTANT: This is a commercial software product
and any kind of using it must agree to the Websplosion's license agreement.
It can be found at http://www.chameleonsocial.com/license.doc

This notice may not be removed from the source code. */

$area = "login";
include("./_include/core/pony_start.php");

CustomPage::setTableColOrder();
CustomPage::checkAccessPage();
$page = new CustomPage('', $g['tmpl']['dir_tmpl_mobile'] . 'page.html');
$page->setTable('col_order');
$header = new CHeader("header", $g['tmpl']['dir_tmpl_mobile'] . "_header.html");
$page->add($header);
$footer = new CFooter("footer", $g['tmpl']['dir_tmpl_mobile'] . "_footer.html");
$page->add($footer);

if (Common::isParseModule('user_menu')) {
    $user_menu = new CUserMenu("user_menu", $g['tmpl']['dir_tmpl_mobile'] . "_user_menu.html");
    if (Common::getOption('set', 'template_options') != 'urban') {
        include("./_include/current/profile_menu.php");
        $profile_menu = new CProfileMenu("profile_menu", $g['tmpl']['dir_tmpl_mobile'] . "_profile_menu.html");
        $profile_menu->setActive('settings');
        $page->add($profile_menu);

        $user_menu->setActive('profile');
        $page->add($user_menu);
    } else {
        $header->add($user_menu);
    }
}

if(get_param('upload_page_content_ajax')) {
    loadPageContentAjax($page);
}

include('./_include/core/main_close.php');