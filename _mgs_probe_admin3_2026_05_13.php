<?php
// Find where $g['main']['admin_password'] is actually set.
set_time_limit(0); @ini_set('display_errors', 1);
$EXPECTED_TOKEN = '429924c65fda7a12ff86d2c73eb838bc';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\n"); }
header('Content-Type: text/plain');

$root = __DIR__;
$needle = 'admin_password';

function grep_recursive($base, $needle, &$hits, $skipdirs = ['ioncube','tmp','staging','_pay','_server','meetgreeksingles.com','_files','m']) {
    if (!is_dir($base)) return;
    $bn = basename($base);
    if (in_array($bn, $skipdirs, true)) return;
    $items = @scandir($base); if (!$items) return;
    foreach ($items as $f) {
        if ($f === '.' || $f === '..') continue;
        $p = $base . '/' . $f;
        if (is_dir($p)) { grep_recursive($p, $needle, $hits, $skipdirs); continue; }
        if (!preg_match('/\.(php|inc|txt|conf|ini)$/i', $f)) continue;
        $sz = @filesize($p);
        if ($sz === false || $sz > 2_000_000) continue;
        $body = @file_get_contents($p);
        if ($body === false) continue;
        if (strpos($body, $needle) !== false) {
            $lines = explode("\n", $body);
            foreach ($lines as $i => $ln) {
                if (strpos($ln, $needle) !== false) {
                    $hits[] = [$p, $i+1, trim($ln)];
                }
            }
        }
    }
}

echo "Grepping for '$needle' under $root...\n\n";
$hits = array();
grep_recursive($root, $needle, $hits);

// De-dupe by path:line:linecontent
$seen = array();
foreach ($hits as $h) {
    [$p, $i, $ln] = $h;
    $key = $p . ':' . $i;
    if (isset($seen[$key])) continue;
    $seen[$key] = true;
    $rel = str_replace($root, '', $p);
    // Censor anything that might be an actual password value
    $cen = preg_replace_callback("/(['\"])([^'\"]{6,})\\1/", function($m) {
        return $m[1] . '<' . strlen($m[2]) . ' chars>' . $m[1];
    }, $ln);
    echo "  $rel:$i\n    $cen\n";
}

echo "\nTotal hits: " . count($seen) . "\n";

// Also check explicitly: does administration_start.php (the file index.php
// includes) reach out to a particular config?
echo "\n== Head of _include/core/administration_start.php ==\n";
$f = $root . '/_include/core/administration_start.php';
if (is_readable($f)) {
    $lines = file($f);
    foreach (array_slice($lines, 0, 60) as $i => $ln) echo str_pad($i+1, 4) . ' ' . rtrim($ln) . "\n";
} else { echo "  not readable\n"; }

echo "\nDONE\n";
