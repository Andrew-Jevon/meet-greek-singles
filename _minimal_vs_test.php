<?php
include("../_include/core/administration_start.php");

class CMin extends CHtmlBlock {
    function parseBlock(&$html) {
        parent::parseBlock($html);
    }
}

$page = new CMin('', $g['tmpl']['dir_tmpl_administration'] . 'help_topic.html');
$header = new CAdminHeader('header', $g['tmpl']['dir_tmpl_administration'] . '_header.html');
$page->add($header);
$footer = new CAdminFooter('footer', $g['tmpl']['dir_tmpl_administration'] . '_footer.html');
$page->add($footer);

include('../_include/core/administration_close.php');
