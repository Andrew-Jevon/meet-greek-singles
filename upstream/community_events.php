<?php
/* (C) Websplosion LLC, 2001-2021

IMPORTANT: This is a commercial software product
and any kind of using it must agree to the Websplosion's license agreement.
It can be found at http://www.chameleonsocial.com/license.doc

This notice may not be removed from the source code. */

include("./_include/core/main_start.php");

checkByAuth();

$cmd = get_param('cmd');
$optionTmplSet = Common::getOption('set', 'template_options');
if (Common::isOptionActive('free_site')
    //|| ($optionTmplSet == 'urban' && !Common::isOptionActive('access_paying'))
    ) {
    redirect(Common::getHomePage());
}

if($optionTmplSet != 'urban' && isUpgraded()) {
    redirect('upgraded.php');
}
if(Common::getOption('upgraded_redirect_to_home_page', 'template_options') && isUpgraded()) {
    $param = array();
    if ($cmd == 'payment_thank') {
        $param = array('cmd' => 'payment_thank');
    }
    redirect(User::url(guid(), null, $param));
}

function isUpgraded() {

    global $g_user;

    $result = false;
    if ($g_user['gold_days'] > 0 and $g_user['type'] != '' and $g_user['type'] != 'none') {
        $option = get_param('option');
        $check = DB::result('SELECT `code` FROM `payment_type` WHERE `type` = ' . to_sql($g_user['type']) . ' and `code` = ' . to_sql($option), 0, 4);
        if ($check != 0 || empty($option)) {
            $cmd = get_param('cmd');
            if ($cmd != 'show' && $cmd != 'save') {
                $result = true;
            }
        }
    }

    return $result;
}

class CGold extends CHtmlBlock {

    function action() {
        $system = get_param('system');
        $item = get_param('item', 1);
        $cmd = get_param('cmd');
        if ($cmd == 'add') {
            echo "test";
            die;
            if ($isAjaxRequest) {
                die(getResponseDataAjaxByAuth($responseData));
            }
        }
    }

    function parseBlock(&$html) {
        global $g;
        global $g_user;
        global $pay;


        parent::parseBlock($html);
    }

}

function isTypePlanImpact() {
    $optionTmplTypePaymentPlan = Common::getOption('type_payment_plan', 'template_options');
    return $optionTmplTypePaymentPlan == 'impact' || $optionTmplTypePaymentPlan == 'edge';
}


$page = new CGold("", getPageCustomTemplate('community_events.html', 'upgrade_template'));
$header = new CHeader("header", $g['tmpl']['dir_tmpl_main'] . "_header.html");
$page->add($header);


if (Common::isParseModule('profile_colum_narrow')){
    $column_narrow = new CProfileNarowBox('profile_column_narrow', $g['tmpl']['dir_tmpl_main'] . '_profile_column_narrow.html');
    $page->add($column_narrow);
}


$footer = new CFooter("footer", $g['tmpl']['dir_tmpl_main'] . "_footer.html");
$page->add($footer);

include("./_include/core/main_close.php");