<?php
/* (C) Websplosion LLC, 2001-2021

IMPORTANT: This is a commercial software product
and any kind of using it must agree to the Websplosion's license agreement.
It can be found at http://www.chameleonsocial.com/license.doc

This notice may not be removed from the source code. */

$area = "login";
include("./_include/core/pony_start.php");

if (!Common::isOptionActiveTemplate('live_enabled')) {
    Common::toHomePage();
}

$isAjaxRequest = get_param('ajax');

if (!$isAjaxRequest) {
	LiveStreaming::checkAviableLiveStreaming();

    LiveStreaming::updateDemoData();
    LiveStreaming::deleteUserBrokenLive();
}

class CPage extends CHtmlBlock
{
    function init()
    {

    }

    function parseBlock(&$html)
    {
        $guid = guid();

        $ajax = get_param('ajax');
        $optionTmplName = Common::getTmplName();
        $uid = User::getParamUid(0);

        $page = get_param_int('page');
        $page = $page < 1 ? 1 : $page;

        $pageTitle = l('page_title');
        $pageDescription = '';
        $pageClass = 'videos_list';
        $pageUrl = Common::pageUrl('live_list');
        $vars = array('page_number' => $page,
                      'page_class'  => $pageClass,
                      'page_title'  => $pageTitle,
                      'page_description' => $pageDescription,
                      'page_user_id'     => 0,
                      'page_guid' => $guid,
                      'url_pages' => $pageUrl,
                      'page_type' => 'lives',
                      'page_filter' => 1,
                      'group_id'    => 0,
                      'group_type'  => ''
                );


		$pagerOnPage = Common::getOptionTemplateInt('list_live_number_items');
        $mOnBar = Common::getOption('usersinfo_pages_per_list', 'template_options');
        $limit = (($page - 1) * $pagerOnPage) . ',' . $pagerOnPage;

        $block = 'list_live';
		$class = "TemplateBase";
		$typeOrderDefault = 'new';

        $online = true;

        LiveStreaming::$isGetDataWithFilter = true;
        $itemsTotal = LiveStreaming::getTotalLive($online, 0);
        LiveStreaming::$isGetDataWithFilter = false;

        $typeOrder = get_param('type_order', $typeOrderDefault);

        if ($ajax) {
			$html->setvar('num_total', $itemsTotal);
        } else {

            $html->assign('', $vars);

            $html->parse('page_filter_tags_hide', false);

            if ($guid) {
                $html->parse('page_filter_only_friends', false);
            }
            if (!$uid) {
                //$html->parse('page_search_query', false);
                $html->parse('page_filter_no_result', false);
                $html->parse('page_filter', false);
            }

			$html->parse('page_title_circle', false);

            $html->parse('wrap_head_links', false);
        }

        LiveStreaming::$isGetDataWithFilter = true;
        $rows = $class::parseListLive($html, $typeOrder, $limit, $block, $online);
        LiveStreaming::$isGetDataWithFilter = false;
        if ($rows) {
            Common::parsePagesListUrban($html, $page, $itemsTotal, $pagerOnPage, $mOnBar, $pageUrl);
        } else {
            $html->parse("list_noitems");
        }

        parent::parseBlock($html);
    }
}

$optionTmplSet = Common::getTmplSet();

$uid = get_param_int('uid');
$dirTmpl = $g['tmpl']['dir_tmpl_mobile'];
$tmplList = array('main'   => $dirTmpl . 'page_list.html',
                  'list'   => $dirTmpl . '_list_page_info.html',
                  'items'  => $dirTmpl . '_list_page_items.html',
                  'item'   => $dirTmpl . '_list_live_item.html',
                  'pages'  => $dirTmpl . '_list_page_pages.html');

if ($isAjaxRequest) {
    $tmplList['main'] = $dirTmpl . 'search_results_ajax.html';
}

$page = new CPage("", $tmplList);

if($isAjaxRequest) {
    getResponsePageAjaxByAuthStop($page, guid());
}

$header = new CHeader("header", $dirTmpl . "_header.html");
$page->add($header);

if (Common::isParseModule('user_menu')) {
    $user_menu = new CUserMenu("user_menu", $g['tmpl']['dir_tmpl_mobile'] . "_user_menu.html");
    if ($optionTmplSet == 'urban') {
        $header->add($user_menu);
    } else {
        $page->add($user_menu);
    }
}

$tmplFooter = $dirTmpl . "_footer.html";
if (Common::isOptionActive('is_allow_empty_footer', 'template_options')) {
    //$tmplFooter = $dirTmpl . "_footer_empty.html";
}
$footer = new CFooter("footer", $tmplFooter);
$page->add($footer);

loadPageContentAjax($page);

include('./_include/core/main_close.php');