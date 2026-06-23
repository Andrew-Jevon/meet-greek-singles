<?php
/* (C) Websplosion LLC, 2001-2021

IMPORTANT: This is a commercial software product
and any kind of using it must agree to the Websplosion's license agreement.
It can be found at http://www.chameleonsocial.com/license.doc

This notice may not be removed from the source code. */

include("../_include/core/administration_start.php");

class CCustomPageEdit extends CHtmlBlock
{
    private $message = '';
    private $table = 'col_order';

	function action()
	{
        global $p;

        $page = get_param('page');
        if (!$page || !DB::count($this->table, '`id` = ' . to_sql($page) . ' OR `parent` = ' .  to_sql($page))) {
            redirect('user_menu_order.php');
        }

		$cmd = get_param('cmd');

		if ($cmd == 'save')
		{
            $lang = get_param('lang');
            $id = get_param('page');
            $isSystem = intval(get_param('system'));
            $pageKey = get_param('page_key');
            $where = '`parent` = ' . to_sql($id) . ' AND `lang` = ' .  to_sql($lang);
            if ($lang == 'default' || $isSystem) {
                $where = '`id` = ' . to_sql($id);
            }

            if (!$isSystem) {
                $data = array(
                    'name' => trim(get_param('name')),
                    'title' => trim(get_param('title')),
                    'content' => trim(get_param('content')),
                );

                if (DB::count($this->table, $where)) {
                    DB::update($this->table, $data, $where);
                } else {
                    $data['lang'] = $lang;
                    $data['parent'] = $id;
                    $data['section'] = get_param('section');
                    DB::insert($this->table, $data, $where);
                }
            }

            $this->uploadIcon($id, 'icon');
            $this->uploadIcon($id . '_selected', 'icon_active');

            if ($isSystem) {
                $posts = array('cmd', 'lang', 'page', 'system', 'section', 'page_key', 'title', 'content');
                foreach ($posts as $key) {
                    unset($_POST[$key]);
                }
                $this->message = updateLanguage($lang, 'all', 'mobile');
            }
            if ($this->message == '') {
                redirect("{$p}?lang={$lang}&page={$id}&action=saved");
            }
		}
	}

	function parseBlock(&$html)
	{
		global $g;

        if ($this->message) {
            $html->setvar('message', $this->message);
            $html->parse('message');
        }

        $lang = Common::getOption('administration', 'lang_value');
        $langTinymceUrl =  $g['tmpl']['url_tmpl_administration'] . "js/tinymce/langs/{$lang}.js";
        if (!file_exists($langTinymceUrl)) {
            $lang = 'default';
        }
        $html->setvar('lang_vw', $lang);

        $id = get_param('page');
        $html->setvar('id', $id);

        $languageCurrent = Common::langParamValue();
        $html->setvar('lang', $languageCurrent);

        adminParseLangsModule($html, $languageCurrent);
        $html->parse('block_language');

        $isSystem = null;
        $pageKey = 'name';

        $language = loadLanguage(get_param('lang', 'default'), 'mobile');

        CustomPage::setTable($this->table);
        $row = CustomPage::loadPageInfo($id, $languageCurrent);
        if ($row) {
            $isSystem = $row['system'];
            $menuTitle = $row['name'];
            if ($isSystem) {
                $menuTitleKey = 'user_menu_' . $row['name'] . CustomPage::getMenuNamePostfix();
                $menuTitle = he_decode(l($menuTitleKey, $language));
                $pageKey = $menuTitleKey;
            }
            $row['name'] = he($menuTitle);
            $html->assign('page', $row);
        }

        $html->setvar('page_key', $pageKey);

        if (!$isSystem) {
            $html->setvar('domain_name', Common::urlSiteSubfolders());
            $html->parse('link_page', false);
            $html->parse('content');
        }

        if(!$isSystem) {

            $tmplName = Common::getTmplName();

            if($tmplName === 'urban') {
                //$this->parseIconUpload($html, $id, 'icon', 'menu_icon');
                //$this->parseIconUpload($html, $id . '_selected', 'icon_active', 'active');
            }

        }

		if (isset(CAdminHeader::$linkToMainMenuAdmin['user_menu_order'])) {
			$html->setvar('section_page',  CAdminHeader::$linkToMainMenuAdmin['user_menu_order']);
		}

		parent::parseBlock($html);
	}

    function parseIconUpload($html, $fileName, $fieldName, $title)
    {
        if(CustomPage::isMenuIconExists($fileName, true)) {
            $html->setvar('rand', rand(0, 100000));
            $html->setvar('url_page_icon', CustomPage::menuIconUrl($fileName, true));
            $html->parse('icon', false);
        }

        $html->setvar('icon_title', l($title));
        $html->setvar('icon_field_name', $fieldName);

        $html->parse('icon_upload');
    }

    function uploadIcon($fileName, $fieldName)
	{
		$icon = false;
		$fileTemp = Common::getOption('dir_files', 'path') . 'temp/admin_upload_icon_' . time() . '_' . rand(0, 1000);
		$fileImageData = Common::uploadDataImage($fileTemp, $fieldName);
		if ($fileImageData) {
			$icon = $fileImageData;
		} elseif (isset($_FILES[$fieldName])) {
			$icon = $_FILES[$fieldName]['tmp_name'];
		}

        if (!empty($icon) && Image::isValid($icon)) {
                $image = new uploadImage($icon);
                if ($image->uploaded) {
                    $image->file_safe_name = false;
                    $image->image_resize = true;
                    $image->image_ratio = true;
                    $image->image_convert = 'png';
                    $image->png_compression = 0;
                    $image->image_y = 32;
                    $image->image_x = 32;
                    $image->file_new_name_body = $fileName;
                    $image->file_new_name_ext = 'png';
                    $image->Process(Common::getOption('dir_tmpl_mobile', 'tmpl') . 'images/menu_icons/');
                    unset($image);
                }
		}

        if($fileImageData && file_exists($fileImageData)) {
            @unlink($fileImageData);
        }

    }

}

$page = new CCustomPageEdit("", $g['tmpl']['dir_tmpl_administration'] . "user_menu_order_edit.html");
$header = new CAdminHeader("header", $g['tmpl']['dir_tmpl_administration'] . "_header.html");
$page->add($header);
$footer = new CAdminFooter("footer", $g['tmpl']['dir_tmpl_administration'] . "_footer.html");
$page->add($footer);
$page->add(new CAdminPageMenuOptions());

include("../_include/core/administration_close.php");