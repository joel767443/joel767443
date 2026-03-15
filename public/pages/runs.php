<?php
$stepsOrder = ['initial_scan', 'tech_stack_detector', 'architecture_detector', 'extract_cv', 'generate_portfolio', 'generate_site'];
$stepLabels = [
    'initial_scan' => 'Initial scan',
    'tech_stack_detector' => 'Tech stack detector',
    'architecture_detector' => 'Architecture detector',
    'extract_cv' => 'Extract CV',
    'generate_portfolio' => 'Generate portfolio',
    'generate_site' => 'Generate site',
];
$rows = $pdo->query('SELECT step, ran_at, output_file FROM pipeline_runs ORDER BY step')->fetchAll(PDO::FETCH_ASSOC);
$byStep = [];
foreach ($rows as $r) {
    $byStep[$r['step']] = $r;
}
?>
<div class="card">
    <h2>Process runs</h2>
    <p class="muted">Last run time per pipeline step (from file mtimes or <code>data/run_log.json</code>).</p>
    <p class="sync-hint"><a href="?sync=1">Refresh run times</a> to update from current file dates.</p>
</div>
<div class="card">
    <table>
        <thead><tr><th>Step</th><th>Last run</th><th>Output file</th></tr></thead>
        <tbody>
        <?php foreach ($stepsOrder as $step): ?>
            <tr>
                <td><?php echo htmlspecialchars($stepLabels[$step] ?? $step); ?></td>
                <td><?php echo isset($byStep[$step]) ? htmlspecialchars($byStep[$step]['ran_at']) : '<span class="muted">—</span>'; ?></td>
                <td><code><?php echo isset($byStep[$step]) ? htmlspecialchars($byStep[$step]['output_file'] ?? '') : '—'; ?></code></td>
            </tr>
        <?php endforeach; ?>
        </tbody>
    </table>
</div>
