<?php
/**
 * Config and DB bootstrap for Developer Intelligence dashboard.
 * Paths are relative to public/ (docroot).
 */
declare(strict_types=1);

$ROOT = dirname(__DIR__);
$DATA_DIR = $ROOT . '/data';
$DB_PATH = $DATA_DIR . '/intelligence.db';
$RUN_LOG_PATH = $DATA_DIR . '/run_log.json';

/**
 * Pipeline step => output file (relative to repo root) for mtime-based run time.
 */
const PIPELINE_STEPS = [
    'initial_scan'        => 'data/projects.json',
    'tech_stack_detector' => 'data/tech_stack.json',
    'architecture_detector' => 'data/architecture.json',
    'extract_cv'          => 'data/cv_extracted.json',
    'generate_portfolio'  => 'portfolio/index.html',
    'generate_site'       => 'site/index.html',
];

function getDb(): PDO
{
    global $DB_PATH, $DATA_DIR;
    if (!is_dir($DATA_DIR)) {
        mkdir($DATA_DIR, 0755, true);
    }
    $dsn = 'sqlite:' . $DB_PATH;
    $pdo = new PDO($dsn, null, null, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
    ]);
    return $pdo;
}

function ensureSchema(PDO $pdo): void
{
    $pdo->exec(<<<'SQL'
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    step TEXT NOT NULL UNIQUE,
    ran_at TEXT NOT NULL,
    output_file TEXT
)
SQL
    );
}

/**
 * Load JSON file; return decoded array or null if missing/invalid.
 */
function loadJson(string $path): ?array
{
    if (!is_file($path)) {
        return null;
    }
    $raw = @file_get_contents($path);
    if ($raw === false) {
        return null;
    }
    $decoded = json_decode($raw, true);
    return is_array($decoded) ? $decoded : null;
}
