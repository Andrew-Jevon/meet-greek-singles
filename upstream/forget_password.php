<?php
/* (C) Websplosion LLC, 2001-2021

IMPORTANT: This is a commercial software product
and any kind of using it must agree to the Websplosion's license agreement.
It can be found at http://www.chameleonsocial.com/license.doc

This notice may not be removed from the source code. */

$area = "public";
if(isset($_GET['login'])){
    unset($area);
}

include("./_include/core/main_start.php");

if(guid()){
    User::logoutWoRedirect();
    redirect($_SERVER['REQUEST_URI']);
}
$area = "public";

$ajax = get_param('ajax');
// 2026-04-25: when forgot_password_redirect_login=Y, the password-reset UX
// is the popup on /login.php. Without this branch a direct GET of this URL
// returns a blank 0-byte body, which looks broken to users who type the URL.
// AJAX calls (with ?ajax=1) still flow through to CForgot as before.
if (!$ajax && Common::isOptionActive('forgot_password_redirect_login', 'template_options')) {
    redirect(Common::pageUrl('login'));
}
if($ajax || Common::isOptionActive('forgot_password_redirect_login', 'template_options')) {
    $forget = new CForgot('', '', '', '', true);
    $forget->action(false);
    echo $forget->message;
    die();
}

$page = new CForgot("", $g['tmpl']['dir_tmpl_main'] . "forget_password.html");


$header = new CHeader("header", $g['tmpl']['dir_tmpl_main'] . "_header.html");
$page->add($header);
$footer = new CFooter("footer", $g['tmpl']['dir_tmpl_main'] . "_footer.html");
$page->add($footer);

include("./_include/core/main_close.php");

?>