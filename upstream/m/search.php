<?php
/* (C) Websplosion LLC, 2001-2021

IMPORTANT: This is a commercial software product
and any kind of using it must agree to the Websplosion's license agreement.
It can be found at http://www.chameleonsocial.com/license.doc

This notice may not be removed from the source code. */

$area = "login";
include("./_include/core/pony_start.php");


$g['to_head'][] = '<link rel="stylesheet" href="'.$g['tmpl']['url_tmpl_mobile'].'css/search.css" type="text/css" media="all"/>';

$langValuesCopyFromOtherSection = array(
    'choose_a_value',
    'filter_data',
    'refine_by_one_of_your_interests',
);

foreach($langValuesCopyFromOtherSection as $langValuesCopyFromOtherSectionKey) {
    if(!isset($l[$p][$langValuesCopyFromOtherSectionKey]) && isset($l['search_results.php'][$langValuesCopyFromOtherSectionKey])) {
        $l[$p][$langValuesCopyFromOtherSectionKey] = $l['search_results.php'][$langValuesCopyFromOtherSectionKey];
    }
}

User::setGetParamsFilter('user_search_filters');

class CSearchAdvanced extends UserFields
{
    function action()
	{
        $cmd = get_param('cmd');
        if(in_array($cmd, array('geo_cities', 'geo_states', 'geo_countries'))) {
            $id = get_param('select_id');
            $selected = get_param('selected');
            $type = str_replace('geo_', '', $cmd);
            $method = 'list' . ucfirst($type);
            $responseData['list'] = Common::$method($id, '', 0);
            die(getResponseDataAjaxByAuth($responseData));
        }
    }

	function parseBlock(&$html)
	{
        $this->parseMobileAdvancedFilter($html);

        $optionTmplName = Common::getOption('name', 'template_options');
        if ($optionTmplName === 'urban_mobile') {
            $this->parseRefireInterests($html);
        }

		parent::parseBlock($html);
	}

    function parseRefireInterests(&$html)
    {
        $sql = "SELECT `id`
                  FROM `col_order`
                 WHERE `name` = 'refine_interests'
                   AND `status` = 'Y'";
        if(DB::result($sql)) {
            CProfileNarowBox::Refine_interests($html);
        }
    }
}

$responseAjax = get_param('ajax');
if($responseAjax) {
    $cmd = get_param('cmd');
    if(in_array($cmd, array('geo_states', 'geo_cities'))) {
        $page = new CSearchAdvanced('', null);
        $page->action(false);
        die();
    }
}

$page = new CSearchAdvanced("", $g['tmpl']['dir_tmpl_mobile'] . "search.html");

if(Common::getTmplSet() === 'urban') {
    $usersFilter = new UsersFilter('users_filter', $g['tmpl']['dir_tmpl_mobile'] . '_list_users_filter.html');
    $usersFilter->setUser(guid());
    $page->add($usersFilter);
}

$header = new CHeader("header", $g['tmpl']['dir_tmpl_mobile'] . "_header.html");
$page->add($header);
$footer = new CFooter("footer", $g['tmpl']['dir_tmpl_mobile'] . "_footer.html");
$page->add($footer);

if (Common::isParseModule('friends_list')) {
    $friends_list = new CFriendsList("friends_list", $g['tmpl']['dir_tmpl_mobile'] . "_friends_list.html");
    $page->add($friends_list);
}

$user_menu = new CUserMenu("user_menu", $g['tmpl']['dir_tmpl_mobile'] . "_user_menu.html");
if (Common::getOption('set', 'template_options') == 'urban') {
    $header->add($user_menu);
} else {
    $user_menu->setActive('search');
    $page->add($user_menu);
}

include("./_include/core/main_close.php");