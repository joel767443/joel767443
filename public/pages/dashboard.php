<?php
$ROOT = dirname(__DIR__, 2);
$DATA_DIR = $ROOT . '/data';
$projects = loadJson($DATA_DIR . '/projects.json') ?? [];
$techStack = loadJson($DATA_DIR . '/tech_stack.json') ?? [];
$architecture = loadJson($DATA_DIR . '/architecture.json') ?? [];
$repoCount = count($projects);
$topLangs = array_slice(array_keys($techStack), 0, 5);
$lastRun = $pdo->query('SELECT step, ran_at FROM pipeline_runs ORDER BY ran_at DESC LIMIT 1')->fetch(PDO::FETCH_ASSOC);
?>
<div class="card">
    <h2>Dashboard</h2>
    <p class="muted">Overview of your developer intelligence data.</p>
</div>
<div class="card">
    <h3>Repositories</h3>
    <p><strong><?php echo (int) $repoCount; ?></strong> projects in <code>data/projects.json</code></p>
</div>
<div class="card">
    <h3>Top languages</h3>
    <p>
        <?php
        foreach ($topLangs as $i => $lang) {
            $pct = $techStack[$lang] ?? 0;
            echo '<span class="badge">' . htmlspecialchars($lang) . ' ' . (is_numeric($pct) ? number_format((float)$pct, 1) . '%' : '') . '</span>';
        }
        ?>
        <?php if (empty($topLangs)): ?>—<?php endif; ?>
    </p>
</div>
<div class="card">
    <h3>Last pipeline run</h3>
    <p>
        <?php if ($lastRun): ?>
            <strong><?php echo htmlspecialchars($lastRun['step']); ?></strong> at <?php echo htmlspecialchars($lastRun['ran_at']); ?>
        <?php else: ?>
            No runs recorded yet. <a href="?sync=1">Refresh run times</a> to infer from file dates.
        <?php endif; ?>
    </p>
</div>
<div class="card">
    <h3>Quick links</h3>
    <p>
        <a href="?page=portfolio" class="btn">View portfolio</a>
        <a href="?page=tech" class="btn">Tech breakdown</a>
        <a href="?page=runs" class="btn">Process runs</a>
    </p>
</div>
