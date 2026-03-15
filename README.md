# GitHub Developer Intelligence

Python tooling that analyzes your GitHub repositories and generates a data-driven portfolio (README, static site, skill graphs) from language stats, architecture detection, and optional CV data.

## Features

- **Repository scan**: Fetches all user repos via GitHub API; aggregates language bytes and README summaries.
- **Tech stack detection**: Languages plus optional framework detection from repo root files (via `scripts/frameworks.json` if present).
- **Architecture detection**: Keyword-based detection (ML, API, microservices, Jamstack, etc.) over repo names, descriptions, topics, and file trees.
- **CV extraction**: Parse LinkedIn-style CV PDF to JSON (`extract_cv.py`) for name, skills, experience, and education.
- **Outputs**: `data/*.json`, `graphs/skills_chart.png`, generated portfolio README (from template), `portfolio/README.md` and `portfolio/index.html`, `site/index.html` and `site/README.md` (portfolio site using `site/css/styles.css`).
- **Optional**: `scripts/deploy.sh` to push generated site and portfolio README to separate remotes; `scripts/test_post.py` for LinkedIn API test post (requires `ACCESS_TOKEN`, `PERSON_ID`).

## Prerequisites

- Python 3.x
- [GitHub Personal Access Token](https://github.com/settings/tokens) (for higher rate limits and private repos)

## Installation

```bash
git clone <repo-url>
cd github-developer-intelligence
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Dependencies** (from `requirements.txt`): `requests`, `python-dotenv`, `matplotlib`, `jinja2`, `ez-parse`, `pdfminer.six`, `markdown`.

## Configuration

1. **Environment**: Copy `example.env` to `.env` and set:
   - `GITHUB_TOKEN` — required for scan and framework/architecture steps.
   - `ACCESS_TOKEN`, `PERSON_ID` — only for LinkedIn test post (`scripts/test_post.py`).

2. **Script-specific**: In `scripts/architecture_detector.py`, set `YOUR_GITHUB_USERNAME` (line 14) if `data/projects.json` does not contain `full_name` for each repo (e.g. if you run an older scan).

3. **Optional files**:
   - `scripts/frameworks.json` — not in repo; if present, `tech_stack_detector.py` uses it for framework/tool detection from repo root file names.
   - `data/skill_categories.json` — created by `generate_portfolio.py` if missing; edit to group skills.
   - `reports/capability_report.txt` — optional; if present, `generate_readme.py` uses "Total Projects:" and "Estimated Complexity Score:" in the generated portfolio README.

## Dashboard (PHP + SQLite)

A local dashboard to view portfolio, tech breakdown, and pipeline run times. Requires PHP 7.4+ with SQLite.

From the repo root:

```bash
php -S localhost:8000 -t public public/index.php
```

Then open [http://localhost:8000](http://localhost:8000). The dashboard provides:

- **Dashboard** — Repo count, top languages, last pipeline run, quick links
- **Portfolio** — Generated portfolio page (iframe + link)
- **Tech breakdown** — Languages, skill categories, detected architectures from `data/*.json`
- **Process runs** — Last run time per pipeline step (from file mtimes or optional `data/run_log.json`)
- **Generated site** — Redirects to the generated profile site

Run times are inferred from output file modification times. Use “Refresh run times” in the nav to re-sync. Optional: add `data/run_log.json` with `{"runs":[{"step":"initial_scan","ran_at":"YYYY-MM-DD HH:MM:SS"},...]}` for explicit run times. SQLite DB: `data/intelligence.db` (created automatically; `data/` is in `.gitignore`).

## Project structure

| Path | Description |
|------|-------------|
| `public/` | PHP dashboard: `index.php` (router), `config.php`, `sync.php`, `layout.php`, `pages/*.php`; run with `php -S localhost:8000 -t public public/index.php` |
| `scripts/` | Python entry points and `common.py` (paths, `load_json`, `render_template`, `get_display_name`, `get_github_user_name`) |
| `data/` | Generated: `projects.json`, `tech_stack.json`, `architecture.json`, `cv_extracted.json`, optional `skill_categories.json`, `intelligence.db`; `data/cache/files/` for architecture file-tree cache |
| `templates/` | `README.template.md`, `site.md`, `site_readme.template.md`, optional CV PDF |
| `site/` | Generated `site/index.html`, `site/README.md`; static `site/css/styles.css`, `site/img/` |
| `portfolio/` | Generated `README.md` and `index.html` (plus skills chart) |
| `reports/` | Optional `capability_report.txt` |
| `graphs/` | Generated `skills_chart.png` |

## Workflow

Run scripts in this order. Later steps depend on outputs from earlier ones.

```mermaid
flowchart LR
  A[initial_scan] --> B[tech_stack_detector]
  B --> C[architecture_detector]
  C --> D[skill_graph]
  D --> E[extract_cv optional]
  E --> F[generate_readme]
  F --> G[generate_portfolio]
  G --> H[generate_site]
  H --> I[deploy optional]
```

1. **initial_scan.py** — Fetches user repos, languages, README summaries; writes `data/projects.json`. Requires `GITHUB_TOKEN`.
2. **tech_stack_detector.py** — Reads `data/projects.json`; aggregates languages, optionally detects frameworks; writes `data/tech_stack.json`.
3. **architecture_detector.py** — Reads `data/projects.json`; fetches file trees (cached in `data/cache/files/`); keyword detection; writes `data/architecture.json`. Set `YOUR_GITHUB_USERNAME` if projects lack `full_name`.
4. **skill_graph.py** — Reads `data/tech_stack.json` and `data/architecture.json`; writes `graphs/skills_chart.png`.
5. **extract_cv.py** (optional) — PDF to `data/cv_extracted.json`; improves name/headline/experience in generated README and site.
6. **generate_readme.py** — Uses `templates/README.template.md`, `data/*.json`, `reports/`; writes **portfolio/README.md** (template-based profile).
7. **generate_portfolio.py** — Writes `portfolio/README.md`, `portfolio/index.html`, `portfolio/skills_chart.png`; uses `data/skill_categories.json` (creates default if missing).
8. **generate_site.py** — Writes `site/index.html` and `site/README.md` from `templates/site.md` and `templates/site_readme.template.md` and data (CV, projects, tech stack, skill categories).
9. **deploy.sh** (optional) — Pushes generated content to separate remotes: creates a `site` branch with site contents and pushes to `site` remote (`main`), then creates a `readme` branch with portfolio README and pushes to `readme` remote (`main`). Requires remotes `site` and `readme` to be configured.

**Example (from repo root):**

```bash
python scripts/initial_scan.py
python scripts/tech_stack_detector.py
python scripts/architecture_detector.py
python scripts/skill_graph.py
python scripts/extract_cv.py templates/cv.pdf    # optional
python scripts/generate_readme.py
python scripts/generate_portfolio.py
python scripts/generate_site.py
./scripts/deploy.sh    # optional: push site and readme to their remotes
```

## Scripts reference

| Script | Purpose | Main inputs | Main outputs |
|--------|---------|-------------|--------------|
| initial_scan | Fetch repos + languages + README summaries | GITHUB_TOKEN | data/projects.json |
| tech_stack_detector | Aggregate languages + detect frameworks | data/projects.json, optional frameworks.json | data/tech_stack.json |
| architecture_detector | Detect architecture patterns | data/projects.json | data/architecture.json |
| skill_graph | Plot skills + architectures | data/tech_stack.json, data/architecture.json | graphs/skills_chart.png |
| extract_cv | Parse CV PDF to JSON | templates/cv.pdf (or path) | data/cv_extracted.json |
| generate_readme | Render portfolio README | templates/README.template.md, data/*, reports/ | portfolio/README.md |
| generate_portfolio | Build portfolio Markdown + HTML | data/*, skill_categories | portfolio/README.md, portfolio/index.html |
| generate_site | Build portfolio site HTML | templates/site.md, templates/site_readme.template.md, data/* | site/index.html, site/README.md |
| deploy | Push site and readme to remotes | site/, portfolio/README.md | (git push to site + readme remotes) |
| test_post | LinkedIn API test post | ACCESS_TOKEN, PERSON_ID | (API call only) |

## Deployment

After generating the site and portfolio, you can push them to separate GitHub repos (e.g. GitHub Pages for the site, profile README repo) using `scripts/deploy.sh`:

1. Add remotes (once):  
   `git remote add site <url-to-site-repo>`  
   `git remote add readme <url-to-readme-repo>`
2. Run the full pipeline (initial_scan → … → generate_site), then:  
   `./scripts/deploy.sh`

The script creates a **site** branch (copies `site/` to repo root, pushes to `site` remote `main`) and a **readme** branch (copies `portfolio/README.md` to repo root, pushes to `readme` remote `main`), then returns to `main` and deletes the temporary branches.

## Outputs

- **Data**: `data/projects.json`, `data/tech_stack.json`, `data/architecture.json`, `data/cv_extracted.json`, `data/skill_categories.json`.
- **Generated content**: `portfolio/README.md` (template-based and/or from generate_portfolio), `portfolio/index.html`, `site/index.html`, `site/README.md`, `graphs/skills_chart.png`.

`.env`, `data/`, `reports/`, `site/`, `portfolio/`, and `graphs/` are in `.gitignore`; generated outputs are local unless you force-add them.

## Customization

- Edit `templates/README.template.md` and `templates/site.md` for narrative and structure.
- Edit `data/skill_categories.json` to group technologies for the portfolio.
- Add `scripts/frameworks.json` (object mapping framework names to list of file patterns) to enable framework detection in `tech_stack_detector.py`.
