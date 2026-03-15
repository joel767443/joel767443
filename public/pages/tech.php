<?php
$ROOT = dirname(__DIR__, 2);
$DATA_DIR = $ROOT . '/data';
$techStack = loadJson($DATA_DIR . '/tech_stack.json') ?? [];
$skillCategories = loadJson($DATA_DIR . '/skill_categories.json') ?? [];
$architecture = loadJson($DATA_DIR . '/architecture.json') ?? [];
?>
<div class="card">
    <h2>Tech breakdown</h2>
    <p class="muted">Languages, frameworks, and architectures from your repositories.</p>
</div>

<div class="card">
    <h3>Languages (from tech_stack.json)</h3>
    <?php if (!empty($techStack)): ?>
    <table>
        <thead><tr><th>Language / tech</th><th>Usage %</th></tr></thead>
        <tbody>
        <?php foreach ($techStack as $name => $pct): ?>
            <tr><td><?php echo htmlspecialchars($name); ?></td><td><?php echo is_numeric($pct) ? number_format((float)$pct, 1) . '%' : htmlspecialchars((string)$pct); ?></td></tr>
        <?php endforeach; ?>
        </tbody>
    </table>
    <?php else: ?>
    <p class="muted">No data. Run <code>tech_stack_detector.py</code>.</p>
    <?php endif; ?>
</div>

<div class="card">
    <h3>Skill categories (frameworks / tools)</h3>
    <?php if (!empty($skillCategories)): ?>
    <?php foreach ($skillCategories as $key => $cat):
        if (!isset($cat['label'], $cat['items']) || !is_array($cat['items'])) continue;
        $items = $cat['items'];
        if ($techStack) {
            $items = array_filter($items, fn($i) => isset($techStack[$i]));
        }
        if (empty($items)) continue;
    ?>
    <p><strong><?php echo htmlspecialchars($cat['label']); ?></strong>: <?php echo implode(', ', array_map('htmlspecialchars', $items)); ?></p>
    <?php endforeach; ?>
    <?php else: ?>
    <p class="muted">No skill categories. Run <code>generate_portfolio.py</code> to create <code>data/skill_categories.json</code>.</p>
    <?php endif; ?>
</div>

<div class="card">
    <h3>Detected architectures</h3>
    <?php if (!empty($architecture['detected_architectures'])): ?>
    <p class="muted">Total repos processed: <?php echo (int)($architecture['total_repos_processed'] ?? 0); ?></p>
    <table>
        <thead><tr><th>Architecture</th><th>Count</th></tr></thead>
        <tbody>
        <?php
        $counts = $architecture['counts'] ?? [];
        foreach ($architecture['detected_architectures'] as $arch): ?>
            <tr><td><?php echo htmlspecialchars($arch); ?></td><td><?php echo (int)($counts[$arch] ?? 0); ?></td></tr>
        <?php endforeach; ?>
        </tbody>
    </table>
    <?php else: ?>
    <p class="muted">No architecture data. Run <code>architecture_detector.py</code>.</p>
    <?php endif; ?>
</div>
