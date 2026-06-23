<?php
/* (C) Websplosion LLC, 2001-2021

IMPORTANT: This is a commercial software product
and any kind of using it must agree to the Websplosion's license agreement.
It can be found at http://www.chameleonsocial.com/license.doc

This notice may not be removed from the source code. */

$area = "login";

include("./_include/core/main_start.php");



$isSocialCalendar = Common::isOptionActiveTemplate('event_social_enabled');
if ($isSocialCalendar) {
    if (!Common::isOptionActive('calendar_enabled', 'edge_events_settings')) {
        Common::redirectFromWithBaseUrl('profile_view');
    }

    $uid = User::getParamUid(0);
    if (!$uid) {
        Common::redirectFromWithBaseUrl('profile_view');
    }
    $p = 'events_calendar.php';
}

if (Common::isParseModule('events_header')) {
    require_once("./_include/current/events/custom_head.php");
}

if (Common::isParseModule('events_header')) {
    require_once("./_include/current/events/header.php");
}

if (Common::isParseModule('events_sidebar')) {
    require_once("./_include/current/events/sidebar.php");
}

if ($isSocialCalendar) {
    require_once("./_include/current/events/tools.php");
    require_once("./_include/current/events/calendar.php");
} else {
    require_once("./_include/current/events/tools.php");
    require_once("./_include/current/events/event_show.php");
    require_once("./_include/current/events/event_image_list.php");
    require_once("./_include/current/events/event_guest_list.php");
    require_once("./_include/current/events/event_comment_list.php");
    require_once("./_include/current/events/event_list.php");
    require_once("./_include/current/events/calendar.php");
}

class CEvents extends CHtmlBlock
{
	function action()
	{
		global $g_user;
        global $l;
        global $g;
	}

	function parseBlock(&$html)
	{
		global $g_user;
		global $l;
		global $g;

        $guid = guid();
        $uid = User::getParamUid();
        if($html->varExists('page_title')){
            $pageTitle = l('your_calendar');
            if ($uid != $guid) {
                $name = User::getInfoBasic($uid, 'name');
                $name = User::nameShort($name);
                $pageTitle = lSetVars('page_title_someones', array('name' => $name));
                $html->setvar('page_title_user_photo', User::getPhotoDefault($uid, 'r'));
                $html->parse('page_title_user_photo', false);

                $html->parse('page_title_header_photo', false);
            }
            $html->setvar('page_title', $pageTitle);
        }

        if($html->varExists('my_calendar_url')){
            $html->setvar('my_calendar_url', Common::pageUrl('user_calendar', $guid));
        }

        TemplateEdge::parseColumn($html, $uid ? $uid : $guid);

		parent::parseBlock($html);
	}
}


$page = new CEvents("", getPageCustomTemplate('events_calendar.html', 'calendar_template'));
$header = new CHeader("header", $g['tmpl']['dir_tmpl_main'] . "_header.html");

if (Common::isParseModule('events_custom_head')) {
    $events_custom_head = new CEventsCustomHead("custom_head", $g['tmpl']['dir_tmpl_main'] . "_events_custom_head.html");
    $header->add($events_custom_head);
}

$page->add($header);

$footer = new CFooter("footer", $g['tmpl']['dir_tmpl_main'] . "_footer.html");
$page->add($footer);

if (Common::isParseModule('events_header')) {
    $events_header = new CEventsHeader("events_header", $g['tmpl']['dir_tmpl_main'] . "_events_header.html");
    $page->add($events_header);
}

if (Common::isParseModule('events_sidebar')) {
    $events_sidebar = new CEventsSidebar("events_sidebar", $g['tmpl']['dir_tmpl_main'] . "_events_sidebar.html");
    $page->add($events_sidebar);
}

$tmpl = $g['tmpl']['dir_tmpl_main'] . "_events_calendar.html";
if ($isSocialCalendar) {
    $tmpl = array(
        'main' => $g['tmpl']['dir_tmpl_main'] . '_events_calendar.html',
        'items' => $g['tmpl']['dir_tmpl_main'] . '_events_calendar_items.html'
    );
}
$events_calendar = new CEventsCalendar("events_calendar", $tmpl);


$page->add($events_calendar);

include("./_include/core/main_close.php");