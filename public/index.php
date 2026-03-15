<?php
/**
 * Front controller: route dashboard pages and static assets.
 * Run: php -S localhost:8000 -t public public/index.php
 */
declare(strict_types=1);

$ROOT = dirname(__DIR__);

// Trigger sync on demand
if (isset($_GET['sync']) && $_GET['sync'] === '1') {
    require_once __DIR__ . '/sync.php';
    $uri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH) ?: '/';
    $q = $_GET;
    unset($q['sync']);
    $query = $q ? '?' . http_build_query($q) : '';
    header('Location: ' . $uri . $query, true, 302);
    exit;
}

$uri = $_SERVER['REQUEST_URI'];
$path = parse_url($uri, PHP_URL_PATH);
$path = $path ?: '/';
$path = preg_replace('#/+#', '/', $path);

// Static asset routes: serve from parent dirs
if (preg_match('#^/portfolio/(.*)$#', $path, $m)) {
    $file = $ROOT . '/portfolio/' . $m[1];
    if (is_file($file) && strpos(realpath($file), realpath($ROOT . '/portfolio')) === 0) {
        $ext = pathinfo($file, PATHINFO_EXTENSION);
        $types = ['html' => 'text/html', 'css' => 'text/css', 'js' => 'application/javascript', 'png' => 'image/png', 'jpg' => 'image/jpeg', 'jpeg' => 'image/jpeg', 'ico' => 'image/x-icon', 'svg' => 'image/svg+xml', 'md' => 'text/markdown'];
        if (isset($types[$ext])) {
            header('Content-Type: ' . $types[$ext]);
        }
        readfile($file);
        exit;
    }
}
if (preg_match('#^/site/(.*)$#', $path, $m)) {
    $file = $ROOT . '/site/' . $m[1];
    if (is_file($file) && strpos(realpath($file), realpath($ROOT . '/site')) === 0) {
        $ext = pathinfo($file, PATHINFO_EXTENSION);
        $types = ['html' => 'text/html', 'css' => 'text/css', 'js' => 'application/javascript', 'png' => 'image/png', 'jpg' => 'image/jpeg', 'jpeg' => 'image/jpeg', 'ico' => 'image/x-icon', 'svg' => 'image/svg+xml'];
        if (isset($types[$ext])) {
            header('Content-Type: ' . $types[$ext]);
        }
        readfile($file);
        exit;
    }
}
if (preg_match('#^/css/(.*)$#', $path, $m)) {
    $file = $ROOT . '/site/css/' . $m[1];
    if (is_file($file) && strpos(realpath($file), realpath($ROOT . '/site/css')) === 0) {
        header('Content-Type: text/css');
        readfile($file);
        exit;
    }
}
if (preg_match('#^/img/(.*)$#', $path, $m)) {
    $file = $ROOT . '/site/img/' . $m[1];
    if (is_file($file) && strpos(realpath($file), realpath($ROOT . '/site/img')) === 0) {
        $ext = pathinfo($file, PATHINFO_EXTENSION);
        $types = ['png' => 'image/png', 'jpg' => 'image/jpeg', 'jpeg' => 'image/jpeg', 'gif' => 'image/gif', 'webp' => 'image/webp', 'svg' => 'image/svg+xml'];
        if (isset($types[$ext])) {
            header('Content-Type: ' . $types[$ext]);
        }
        readfile($file);
        exit;
    }
}

// Dashboard pages
$page = $_GET['page'] ?? 'dashboard';
$allowed = ['dashboard', 'portfolio', 'tech', 'runs', 'profile'];
if (!in_array($page, $allowed, true)) {
    $page = 'dashboard';
}

if ($page === 'profile') {
    header('Location: /site/index.html', true, 302);
    exit;
}

require_once __DIR__ . '/config.php';
$pdo = getDb();
ensureSchema($pdo);
$runCount = (int) $pdo->query('SELECT COUNT(*) FROM pipeline_runs')->fetchColumn();
if ($runCount === 0) {
    require_once __DIR__ . '/sync.php';
}

$pageTitle = [
    'dashboard' => 'Dashboard',
    'portfolio' => 'Portfolio',
    'tech' => 'Tech breakdown',
    'runs' => 'Process runs',
    'profile' => 'Generated site',
][$page];

ob_start();
include __DIR__ . '/layout.php';
echo ob_get_clean();
