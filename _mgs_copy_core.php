<?php
// One-shot: copy production _include/core/* into staging _include/core/.
// Both dirs live under /home/slqihj5q4r69/public_html/ and are owned by the same user,
// so PHP running as that user (or Apache's group equivalent) can read prod and write staging.
set_time_limit(0);
@ini_set('memory_limit', '512M');
@ini_set('display_errors', 1);
error_reporting(E_ALL);

$EXPECTED_TOKEN = 'eb8f8038d4b7d3912f65606243fc926e';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) {
    http_response_code(403); exit("forbidden\n");
}

$SRC = '/home/slqihj5q4r69/public_html/_include/core';
$DST = __DIR__ . '/_include/core'; // this script lives in staging webroot

header('Content-Type: text/plain');

if (!is_dir($SRC)) {
    http_response_code(500);
    exit("src_not_found: $SRC\n");
}

if (!@mkdir($DST, 0755, true) && !is_dir($DST)) {
    http_response_code(500);
    exit("cant_create_dst: $DST\n");
}

$copied = 0; $errors = array(); $total_bytes = 0;

function recurseCopy($src, $dst, &$copied, &$errors, &$total_bytes) {
    if (!is_dir($src)) {
        $errors[] = "not_dir: $src";
        return;
    }
    if (!is_dir($dst)) {
        if (!@mkdir($dst, 0755, true)) {
            $errors[] = "mkdir_fail: $dst";
            return;
        }
    }
    $dh = @opendir($src);
    if (!$dh) { $errors[] = "opendir_fail: $src (perms?)"; return; }
    while (($name = readdir($dh)) !== false) {
        if ($name === '.' || $name === '..') continue;
        $s = $src . '/' . $name;
        $d = $dst . '/' . $name;
        if (is_dir($s)) {
            recurseCopy($s, $d, $copied, $errors, $total_bytes);
        } else {
            if (@copy($s, $d)) {
                $copied++;
                $total_bytes += filesize($d);
            } else {
                $err = error_get_last();
                $errors[] = "copy_fail: $s -> $d (" . ($err['message'] ?? 'unknown') . ")";
            }
        }
    }
    closedir($dh);
}

recurseCopy($SRC, $DST, $copied, $errors, $total_bytes);

echo "OK\n";
echo "src: $SRC\n";
echo "dst: $DST\n";
echo "files_copied: $copied\n";
echo "total_bytes: $total_bytes\n";
if ($errors) {
    echo "errors:\n";
    foreach (array_slice($errors, 0, 10) as $e) echo "  $e\n";
    if (count($errors) > 10) echo "  ... and " . (count($errors) - 10) . " more\n";
}
