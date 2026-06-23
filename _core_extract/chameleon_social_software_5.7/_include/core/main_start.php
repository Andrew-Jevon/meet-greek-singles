<?php
/* (C) Websplosion LLC, 2001-2021

IMPORTANT: This is a commercial software product
and any kind of using it must agree to the Websplosion's license agreement.
It can be found at http://www.chameleonsocial.com/license.doc

This notice may not be removed from the source code. */

include_once(__DIR__ . '/starter.php');
include_once(__DIR__ . '/start.php');

$routerLoadCore = isset($g['router']) && intval($g['router']['load_core']);

if (!$routerLoadCore && $p != 'updater.php') {
    Social::init();
    include(__DIR__ . '/main_auth.php');
}