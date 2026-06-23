<?php
$EXPECTED_TOKEN = '10c51fe280e02f20a33c38779f0c2ad4';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit; }
header('Content-Type: text/plain');
echo "=== whoami ===\n";
echo "posix_getuid: " . (function_exists('posix_getuid') ? posix_getuid() : 'n/a') . "\n";
echo "get_current_user: " . get_current_user() . "\n";
echo "getenv USER: " . getenv('USER') . "\n";
echo "script_path: " . __FILE__ . "\n";
echo "cwd: " . getcwd() . "\n";
echo "\n=== file_exists checks ===\n";
$paths = array(
    '/home/slqihj5q4r69',
    '/home/slqihj5q4r69/public_html',
    '/home/slqihj5q4r69/public_html/_include',
    '/home/slqihj5q4r69/public_html/_include/core',
    '/home/slqihj5q4r69/public_html/_include/core/main_start.php',
    '/home/slqihj5q4r69/public_html/index.php',
    '/home/slqihj5q4r69/public_html/staging/_include/core',
);
foreach ($paths as $p) {
    $exists = file_exists($p) ? 'YES' : 'no';
    $readable = is_readable($p) ? 'yes' : 'no';
    $is_dir = is_dir($p) ? 'dir' : (is_file($p) ? 'file' : '—');
    $perms = @fileperms($p);
    echo "  $p\n    exists=$exists readable=$readable kind=$is_dir perms=" . ($perms === false ? '?' : sprintf('%o', $perms & 0777)) . "\n";
}

echo "\n=== listing production public_html (via PHP) ===\n";
$d = @opendir('/home/slqihj5q4r69/public_html');
if ($d) {
    $files = array();
    while (($n = readdir($d)) !== false) $files[] = $n;
    closedir($d);
    sort($files);
    foreach (array_slice($files, 0, 40) as $f) {
        echo "  " . $f . (is_dir('/home/slqihj5q4r69/public_html/' . $f) ? '/' : '') . "\n";
    }
    echo "  (total " . count($files) . " entries)\n";
} else {
    echo "  opendir failed\n";
}
