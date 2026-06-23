<?php
/* (C) Websplosion LLC, 2001-2021

IMPORTANT: This is a commercial software product
and any kind of using it must agree to the Websplosion's license agreement.
It can be found at http://www.chameleonsocial.com/license.doc

This notice may not be removed from the source code. */

$g['no_headers'] = true;
$g['mobile_redirect_off'] = true;

include("./_include/core/main_start.php");

$photoId = get_param_int('photo_id');
$photo = array();
$filename = false;
if ($photoId) {
    $where = '`photo_id` = ' . to_sql($photoId);
    $isSiteAdministrator = Common::isSiteAdministrator();
    if(!$isSiteAdministrator) {
        $where .= ' AND `user_id` = ' . to_sql(guid());
    }
	$photo = DB::one('photo', $where);
	if ($photo) {
        if($isSiteAdministrator) {
            $photo['private'] = 'N';
        }
		$filename = $g['path']['dir_files'] . User::getPhotoFile($photo, 'src', '');
		$part = explode('?', $filename);//no version
		$filename = $part[0];
	}
}
$ext = 'jpg';
if ($filename && file_exists($filename)) {
	CProfilePhoto::createFileOrigImage($filename);

    $headers = apache_request_headers();
    $filemtime = gmdate('D, d M Y H:i:s', filemtime($filename)) . ' GMT';

    if (isset($headers['If-Modified-Since']) && ($headers['If-Modified-Since'] == $filemtime)) {
        header('Last-Modified: ' . $filemtime, true, 304);
    } else {

        header('Pragma: public');
        header('Cache-Control: max-age=86400');
        header('Expires: '. gmdate('D, d M Y H:i:s \G\M\T', time() + 86400));

        header('Last-Modified: ' . $filemtime, true, 200);

        // Fix mime-type for IE on some server configurations
        if($ext == 'jpg') {
            $ext = 'jpeg';
        }

        header('Content-Type: image/' . $ext);

		$im = new Image();
		$im->loadImage($filename);

        $imageSideSize = 2000;

        if($im->getHeight() > $imageSideSize || $im->getWidth() > $imageSideSize) {
    //        $imageSizes = array();
    //        $imageSizeSubTypes = array('x', 'y');
    //        foreach(CProfilePhoto::$sizesBasePhoto as $imageSizeType) {
    //            foreach($imageSizeSubTypes as $imageSizeSubType) {
    //                $imageSizes[] = intval(trim(Common::getOption($imageSizeType . '_' . $imageSizeSubType, 'image')));
    //            }
    //        }
    //
    //        $maxImageSize = max($imageSizes);
    //        $imageSideSize = min(2000, $maxImageSize);

            $im->resizeWH($imageSideSize, $imageSideSize, false, '', 0, '', '', false);
            imageJpeg($im->image, null, $g['image']['quality']);
            $im->clearImage();
        } else {
            //header('Content-Length: ' . filesize($filename));
            readfile($filename);
        }
    }
} else {
    header("HTTP/1.0 404 Not Found");
}