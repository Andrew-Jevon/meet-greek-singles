<?php
/* (C) Websplosion LLC, 2001-2021

IMPORTANT: This is a commercial software product
and any kind of using it must agree to the Websplosion's license agreement.
It can be found at http://www.chameleonsocial.com/license.doc

This notice may not be removed from the source code. */

$area = "login";
include("./_include/core/main_start.php");
require_once("./_include/current/places/tools.php");

$from = isset($_SERVER['HTTP_REFERER']) ? $_SERVER['HTTP_REFERER'] : Common::getHomePage();

CPlacesTools::delete_place(get_param('id', ''), false);

redirect($from);