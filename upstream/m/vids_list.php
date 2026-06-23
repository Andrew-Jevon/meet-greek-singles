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

if (!$isAjaxRequest && $p == 'live_list_finished.php') {
	LiveStreaming::checkAviableLiveStreaming();
}

class CPage extends CHtmlBlock
{
    function init()
    {

    }

    function parseBlock(&$html)
    {
		global $p;

        $guid = guid();

		$isPageLiveFinished = $p == 'live_list_finished.php';
		if ($isPageLiveFinished) {
			$html->setvar('guid', guid());
		}

        $ajax = get_param('ajax');
        $optionTmplName = Common::getTmplName();
		$isEdge = $optionTmplName == 'edge';

        $uid = User::getParamUid(0);

        $groupsPhotoList = Groups::getParamTypeContentList();
        $isPagesPhotosList = $groupsPhotoList == 'group_page';
        if ($groupsPhotoList) {
            $groupId = 0;
        } else {
            $groupId = Groups::getParamId();
            if ($groupId) {
                $groupInfo = Groups::getInfoBasic($groupId);
                if (!$groupInfo) {
                    $groupId = 0;
                }
            }
        }

        $page = get_param_int('page');
        $page = $page < 1 ? 1 : $page;

        $pageTitle = l('page_title');
        $pageDescription = '';
        $pageClass = 'videos_list';

		if ($isPageLiveFinished) {
			$pageUrl = Common::pageUrl('live_list_finished');
		} else {
			$pageUrl = Common::pageUrl('vids_list');
		}

        $vars = array('page_number' => $page,
                      'page_class'  => $pageClass,
                      'page_title'  => $pageTitle,
                      'page_description' => $pageDescription,
                      'page_user_id'     => $uid,
                      'page_guid' => $guid,
                      'url_pages' => $pageUrl,
                      'page_type' => 'videos',
                      'page_filter' => intval(!$uid),
                      'group_id'    => $groupId,
                      'group_type'  => $groupsPhotoList ? $groupsPhotoList : ''
                );

		$pagerOnPage = Common::getOptionTemplateInt('list_live_number_items');
        $mOnBar = Common::getOption('usersinfo_pages_per_list', 'template_options');

        $limit = (($page - 1) * $pagerOnPage) . ',' . $pagerOnPage;

        $block = 'list_video';
        $class = "TemplateBase";
		$typeOrderDefault = 'new';


        CProfileVideo::$isGetDataWithFilter = true;
        $itemsTotal = CProfileVideo::getTotalVideos($uid, $groupId);
        CProfileVideo::$isGetDataWithFilter = false;

        $typeOrder = get_param('type_order', $typeOrderDefault);

        if (!$ajax) {
            $html->assign('', $vars);

            $show = get_param('show');
            if ($show == 'video_gallery') {
                $html->setvar('show_video_id', get_param_int('video_id'));
                $html->setvar('show_comment_id', get_param_int('cid'));
                $html->parse('show_video_gallery_js', false);
            }
        } else {
            $html->setvar('num_total', $itemsTotal);
        }

        CProfileVideo::$isGetDataWithFilter = true;
        $rows = $class::parseListVideos($html, $typeOrder, $limit, $block, $groupId, true);
        CProfileVideo::$isGetDataWithFilter = false;
        if ($rows) {
            Common::parsePagesListUrban($html, $page, $itemsTotal, $pagerOnPage, $mOnBar, $pageUrl);
        } else {
            $html->parse("list_noitems");
        }

        if ($guid && $ajax && !$uid) {
            User::updateUserFilter($filter);
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
                  'item'   => $dirTmpl . '_list_vids_item.html',
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