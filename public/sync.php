<?php
/**
 * Sync pipeline_runs from file mtimes and optional data/run_log.json.
 * Run from CLI: php sync.php
 * Or from web: index.php?sync=1 (called from front controller).
 */
declare(strict_types=1);

require_once __DIR__ . '/config.php';

$ROOT = dirname(__DIR__);

function getRunLogTimes(string $path): array
{
    $data = loadJson($path);
    if (!$data || !isset($data['runs']) || !is_array($data['runs'])) {
        return [];
    }
    $byStep = [];
    foreach ($data['runs'] as $entry) {
        if (isset($entry['step'], $entry['ran_at'])) {
            $byStep[$entry['step']] = $entry['ran_at'];
        }
    }
    return $byStep;
}

function syncPipelineRuns(string $root): void
{
    $pdo = getDb();
    ensureSchema($pdo);

    $runLogPath = $root . '/data/run_log.json';
    $runLogTimes = getRunLogTimes($runLogPath);

    $stmt = $pdo->prepare('INSERT OR REPLACE INTO pipeline_runs (step, ran_at, output_file) VALUES (?, ?, ?)');

    foreach (PIPELINE_STEPS as $step => $outputFile) {
        $fullPath = $root . '/' . $outputFile;
        $ranAt = null;

        if (isset($runLogTimes[$step])) {
            $ranAt = $runLogTimes[$step];
        } elseif (is_file($fullPath)) {
            $ts = filemtime($fullPath);
            $ranAt = date('Y-m-d H:i:s', $ts);
        }

        if ($ranAt !== null) {
            $stmt->execute([$step, $ranAt, $outputFile]);
        }
    }
}

syncPipelineRuns($ROOT);

if (php_sapi_name() === 'cli') {
    echo "Sync complete.\n";
}
