<?php
$EXPECTED_TOKEN = '51c0b4023177421a32e57c165e1d4503';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit; }
header('Content-Type: text/plain');

echo "=== list _include/ via PHP ===\n";
$d = @opendir('/home/slqihj5q4r69/public_html/_include');
if ($d) {
    while (($n = readdir($d)) !== false) {
        $p = '/home/slqihj5q4r69/public_html/_include/' . $n;
        echo "  $n" . (is_dir($p) ? '/' : '') . " (readable=" . (is_readable($p) ? 'Y' : 'N') . ")\n";
    }
    closedir($d);
}
echo "\n=== try file_get_contents on core ===\n";
$paths = array(
    '/home/slqihj5q4r69/public_html/_include/core/main_start.php',
    '/home/slqihj5q4r69/public_html/_include/core',
);
foreach ($paths as $p) {
    $r = @file_get_contents($p, false, null, 0, 200);
    echo "  $p: " . ($r === false ? 'FAILED (' . (error_get_last()['message'] ?? '?') . ')' : 'READ ' . strlen($r) . ' bytes') . "\n";
}

echo "\n=== include_path + open_basedir ===\n";
echo "include_path: " . get_include_path() . "\n";
echo "open_basedir: " . ini_get('open_basedir') . "\n";

echo "\n=== try glob + scandir ===\n";
echo "glob _include/*/main_start.php:\n";
foreach (glob('/home/slqihj5q4r69/public_html/_include/*/main_start.php') as $m) echo "  $m\n";
echo "scandir _include/:\n";
$s = @scandir('/home/slqihj5q4r69/public_html/_include');
if ($s) foreach ($s as $n) echo "  $n\n";

echo "\n=== try chdir + relative include on index.php ===\n";
chdir('/home/slqihj5q4r69/public_html');
echo "file_exists('./_include/core/main_start.php'): " . (file_exists('./_include/core/main_start.php') ? 'YES' : 'NO') . "\n";
// Try as if it were an include attempt
$test = @include('./_include/core/main_start.php');
echo "@include returned: " . var_export($test, true) . "\n";
$err = error_get_last();
if ($err) echo "last_err: " . $err['message'] . "\n";
