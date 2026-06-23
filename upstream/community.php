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
        global $g, $g_user, $p;
        $system = get_param('system');
        $item = get_param('item', 1);
        $cmd = get_param('cmd');
        if ($cmd == 'add') {
            $nm = get_param('fullName');
            $email = get_param('email');
            $location = get_param('location');
            $activeMember = get_param('activeMember');
            $interest = get_param('interest');
            $experience = get_param('experience');
            $additional = get_param('additional');
            
            // --- NEW: Handle the checkbox array ---
            $eventsRaw = get_param('events');
            // If multiple checkboxes are selected, join them with a comma. 
            // If it's somehow not an array, just use the raw value.
            $eventsFormatted = is_array($eventsRaw) ? implode(', ', $eventsRaw) : (string)$eventsRaw;
            
            // Get the currently logged-in user's ID
            $userId = guid(); 

            // Construct the SQL query using the formatted events string
            $sql = "INSERT INTO `custom_event_applications` (
                        `user_id`, `full_name`, `email`, `location`, `active_member`, 
                        `interest`, `experience`, `additional`, `events`, `created_at`
                    ) VALUES (
                        " . to_sql($userId, 'Number') . ",
                        " . to_sql($nm) . ",
                        " . to_sql($email) . ",
                        " . to_sql($location) . ",
                        " . to_sql($activeMember) . ",
                        " . to_sql($interest) . ",
                        " . to_sql($experience) . ",
                        " . to_sql($additional) . ",
                        " . to_sql($eventsFormatted) . ", 
                        NOW()
                    )";

            // Execute the query
            DB::execute($sql);

            $emailDetails = "A new event application has been submitted:\n\n";
            $emailDetails .= "Name: " . $nm . "\n";
            $emailDetails .= "Email: " . $email . "\n";
            $emailDetails .= "Location: " . $location . "\n";
            $emailDetails .= "Active Member: " . $activeMember . "\n";
            $emailDetails .= "Interest: " . $interest . "\n";
            $emailDetails .= "Experience: " . $experience . "\n";
            $emailDetails .= "Selected Events: " . $eventsFormatted . "\n";
            $emailDetails .= "Additional Info: " . $additional . "\n";

            // 3. Send the Email Notification to Admin
            if (Common::isEnabledAutoMail('contact')) {
                $vars = array(
                    'title'   => 'New Event Application: ' . $nm,
                    'name'    => $nm,
                    'from'    => $email,
                    'comment' => nl2br($emailDetails) // Use nl2br to convert \n to <br> for HTML emails
                );
                
                // Send to the site info email address
                Common::sendAutomail(
                    Common::getOption('administration', 'lang_value'), 
                    $g['main']['info_mail'], 
                    'contact', 
                    $vars
                );
            }

            // Handle the response
            // if ($isAjaxRequest) {
            //     // Return success state for AJAX submission
            //     $responseData = true; 
            //     die(getResponseDataAjaxByAuth($responseData));
            // } else {
                // Standard form submit redirect
                redirect('community.php?success=1'); 
            // }
        }
    }

    function parseBlock(&$html) {
        global $g;
        global $g_user;
        global $pay;
        $success = get_param('success');
        if($success)
        {
            $html->setvar('success', '<div class="alert alert-success"><p>Your query has been submitted successfully.</p></div>');
        }
        else
        {
            $html->setvar('success', '');
        }
        

        parent::parseBlock($html);
    }

}

function isTypePlanImpact() {
    $optionTmplTypePaymentPlan = Common::getOption('type_payment_plan', 'template_options');
    return $optionTmplTypePaymentPlan == 'impact' || $optionTmplTypePaymentPlan == 'edge';
}


$page = new CGold("", getPageCustomTemplate('community.html', 'upgrade_template'));
$header = new CHeader("header", $g['tmpl']['dir_tmpl_main'] . "_header.html");
$page->add($header);


if (Common::isParseModule('profile_colum_narrow')){
    $column_narrow = new CProfileNarowBox('profile_column_narrow', $g['tmpl']['dir_tmpl_main'] . '_profile_column_narrow.html');
    $page->add($column_narrow);
}


$footer = new CFooter("footer", $g['tmpl']['dir_tmpl_main'] . "_footer.html");
$page->add($footer);

include("./_include/core/main_close.php");