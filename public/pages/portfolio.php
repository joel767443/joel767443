<?php
$ROOT = dirname(__DIR__, 2);
$portfolioPath = $ROOT . '/portfolio/index.html';
?>
<div class="card">
    <h2>Portfolio</h2>
    <p class="muted">Generated portfolio (from <code>generate_portfolio.py</code>).</p>
    <p>
        <a href="/portfolio/index.html" target="_blank" rel="noopener" class="btn">Open portfolio in new tab</a>
    </p>
</div>
<?php if (is_file($portfolioPath)): ?>
<iframe src="/portfolio/index.html" title="Generated portfolio" style="width:100%; height:80vh; border:1px solid #334155; border-radius:10px; background:#0f172a;"></iframe>
<?php else: ?>
<p class="muted">Portfolio not generated yet. Run <code>python scripts/generate_portfolio.py</code>.</p>
<?php endif; ?>
