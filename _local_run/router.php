<?php
// Dev router for PHP built-in server — mirrors Chameleon's .htaccess:
//   RewriteCond !-f ; RewriteCond !-d ; RewriteRule ^(.*)$ router.php?name_seo=$1

// Spoof the production hostname/HTTPS (matches Irene\_local\router.php) so the
// ionCube domain-locked license validates instantly and FB/URL logic stays on
// the prod domain — otherwise the first cold request hangs on a network check.
$_SERVER['HTTP_HOST']   = 'meetgreeksingles.com';
$_SERVER['SERVER_NAME'] = 'meetgreeksingles.com';
$_SERVER['HTTPS']       = 'on';
$_SERVER['SERVER_PORT'] = '443';

$root   = __DIR__ . '/webroot';
$rootRp = realpath($root);
$uri    = urldecode(parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH));
$path   = realpath($root . $uri);
$inRoot = $path && strpos($path, $rootRp) === 0;

// 1. Existing static (non-PHP) file -> let the built-in server serve it as-is.
if ($inRoot && is_file($path)) {
    if (strtolower(pathinfo($path, PATHINFO_EXTENSION)) !== 'php') {
        return false;
    }
    // Existing .php file -> execute it directly.
    chdir(dirname($path));
    require $path;
    return true;
}

// 2. Site root -> DirectoryIndex index.php
if ($uri === '/' || $uri === '') {
    chdir($root);
    require $root . '/index.php';
    return true;
}

// 3. Existing directory with an index.php
if ($inRoot && is_dir($path) && is_file($path . '/index.php')) {
    chdir($path);
    require $path . '/index.php';
    return true;
}

// 4. MultiViews emulation: /login -> login.php, /m/join -> m/join.php, etc.
$phpCandidate = realpath($root . $uri . '.php');
if ($phpCandidate && strpos($phpCandidate, $rootRp) === 0 && is_file($phpCandidate)) {
    chdir(dirname($phpCandidate));
    require $phpCandidate;
    return true;
}

// 5. Static SEO pages that have no matching .php file (mirrors Common::pageUrl's $urls map).
$seo = ltrim($uri, '/');
$seoMap = [
    'login'                => 'join.php?cmd=please_login',
    'terms'                => 'info.php?page=term_cond',
    'privacy_policy'       => 'info.php?page=priv_policy',
    'encounters'           => 'search_results.php?display=encounters',
    'hot_or_not'           => 'search_results.php?display=encounters',
    'rate_people'          => 'search_results.php?display=rate_people',
    'mutual_likes'         => 'mutual_attractions.php',
    'whom_you_like'        => 'mutual_attractions.php?cmd=whom_you_like',
    'who_likes_you'        => 'mutual_attractions.php?cmd=who_likes_you',
    'private_photo_access' => 'my_friends.php',
    'profile_boost'        => 'upgrade.php?action=refill_credits',
    'refill_credits'       => 'upgrade.php?action=refill_credits',
];
if (isset($seoMap[$seo])) {
    $target = $seoMap[$seo];
    $script = strtok($target, '?');
    $query  = (string) substr(strstr($target, '?'), 1);
    if ($query !== '') {
        parse_str($query, $mapped);
        $_GET = array_merge($mapped, $_GET);        // existing query params (QSA) win
        $_REQUEST = array_merge($mapped, $_REQUEST);
    }
    chdir($root);
    require $root . '/' . $script;
    return true;
}

// 6. Fallback: pretty/SEO URL -> app's own router.php?name_seo=<path> (profiles/groups)
$_GET['name_seo']     = $seo;
$_REQUEST['name_seo'] = $seo;
chdir($root);
require $root . '/router.php';
return true;
