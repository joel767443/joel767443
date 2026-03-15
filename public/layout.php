<?php
/**
 * Shared layout: nav menu + main content.
 * Expects $page, $pageTitle, $pdo (and optional $ROOT from config).
 */
$currentPage = $page;
$navItems = [
    'dashboard' => ['Dashboard', '?page=dashboard'],
    'portfolio' => ['Portfolio', '?page=portfolio'],
    'tech' => ['Tech breakdown', '?page=tech'],
    'runs' => ['Process runs', '?page=runs'],
    'profile' => ['Generated site', '?page=profile'],
];
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title><?php echo htmlspecialchars($pageTitle); ?> – Developer Intelligence</title>
    <style>
        * { box-sizing: border-box; }
        body { margin: 0; font-family: system-ui, sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; }
        .nav { background: #1e293b; padding: 0.75rem 1rem; border-bottom: 1px solid #334155; }
        .nav-inner { max-width: 1200px; margin: 0 auto; display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; }
        .nav a { color: #94a3b8; text-decoration: none; padding: 0.5rem 0.75rem; border-radius: 6px; }
        .nav a:hover { color: #f1f5f9; background: #334155; }
        .nav a.active { color: #22c55e; font-weight: 600; }
        .nav .brand { font-weight: 700; color: #f1f5f9; margin-right: 1rem; }
        main { max-width: 1200px; margin: 0 auto; padding: 1.5rem 1rem 3rem; }
        .card { background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 1rem 1.25rem; margin-bottom: 1rem; }
        .card h2 { margin: 0 0 0.5rem; font-size: 1.1rem; }
        .card h3 { margin: 1rem 0 0.5rem; font-size: 1rem; color: #94a3b8; }
        .muted { color: #94a3b8; font-size: 0.9rem; }
        table { width: 100%; border-collapse: collapse; }
        th, td { text-align: left; padding: 0.5rem 0.75rem; border-bottom: 1px solid #334155; }
        th { color: #94a3b8; font-weight: 500; }
        .badge { display: inline-block; padding: 0.2rem 0.5rem; background: #334155; border-radius: 4px; font-size: 0.8rem; margin: 0.15rem; }
        a.btn { display: inline-block; padding: 0.5rem 1rem; background: #22c55e; color: #0f172a; text-decoration: none; border-radius: 6px; font-weight: 500; margin-top: 0.5rem; }
        a.btn:hover { background: #16a34a; }
        .sync-hint { font-size: 0.85rem; color: #64748b; margin-top: 0.5rem; }
        .sync-hint a { color: #38bdf8; }
    </style>
</head>
<body>
    <nav class="nav">
        <div class="nav-inner">
            <span class="brand">Developer Intelligence</span>
            <?php foreach ($navItems as $key => $item): ?>
                <a href="<?php echo htmlspecialchars($item[1]); ?>" class="<?php echo $key === $currentPage ? 'active' : ''; ?>"><?php echo htmlspecialchars($item[0]); ?></a>
            <?php endforeach; ?>
            <a href="?sync=1" class="sync-hint" style="margin-left:auto;">Refresh run times</a>
        </div>
    </nav>
    <main>
        <?php
        $pageFile = __DIR__ . '/pages/' . $currentPage . '.php';
        if (is_file($pageFile)) {
            include $pageFile;
        } else {
            echo '<p>Page not found.</p>';
        }
        ?>
    </main>
</body>
</html>
