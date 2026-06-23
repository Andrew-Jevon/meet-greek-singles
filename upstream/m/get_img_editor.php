<?php
/* (C) Websplosion LLC, 2001-2021

IMPORTANT: This is a commercial software product
and any kind of using it must agree to the Websplosion's license agreement.
It can be found at http://www.chameleonsocial.com/license.doc

This notice may not be removed from the source code. */

$g['no_headers'] = true;

include("./_include/core/pony_start.php");

$photoId = get_param_int('photo_id');
$photo = array();
$filename = false;
if ($photoId) {
	$photo = DB::one('photo', '`photo_id` = ' . to_sql($photoId));
	if ($photo) {
		$filename = $g['path']['url_files'] . User::getPhotoFile($photo, 'src', '');
		$part = explode('?', $filename);//no version
		$filename = $part[0];
	}
}
$ext = 'jpg';
if ($filename && file_exists($filename)) {
	$filenameOrig = str_replace('_src', '_orig', $filename);
	if (!file_exists($filenameOrig)) {
		@copy($filename, $filenameOrig);
		@chmod($filenameOrig, 0777);
		Common::saveFileSize($filenameOrig);
	}

    $headers = apache_request_headers();
    $filemtime = gmdate('D, d M Y H:i:s', filemtime($filename)) . ' GMT';

    if (isset($headers['If-Modified-Since']) && ($headers['If-Modified-Since'] == $filemtime)) {
        header('Last-Modified: ' . $filemtime, true, 304);
    } else {

        header('Pragma: public');
        header('Cache-Control: max-age=86400');
        header('Expires: '. gmdate('D, d M Y H:i:s \G\M\T', time() + 86400));

        header('Last-Modified: ' . $filemtime, true, 200);
        header('Content-Length: ' . filesize($filename));

        // Fix mime-type for IE on some server configurations
        if($ext == 'jpg') {
            $ext = 'jpeg';
        }

        header('Content-Type: image/' . $ext);
        echo file_get_contents($filename);
    }
} else {
    header("HTTP/1.0 404 Not Found");
}