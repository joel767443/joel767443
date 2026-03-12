## GitHub Developer Intelligence

This repo contains small utilities to analyze your own GitHub repositories and surface high-level insights about your personal codebase.

- **`scripts/initial_scan.py`**: Fetches all repositories for the authenticated user, computes per-repo language percentages, prints a global language breakdown, and saves structured data to `data/projects.json`.
- **`scripts/architecture_detector.py`**: Reads `data/projects.json`, applies simple keyword-based heuristics to infer common architecture patterns across your repos, and writes them to `data/architecture.json`.
- **`scripts/tech_stack_detector.py`**: Reads `data/projects.json`, queries the GitHub API for repo contents, and combines language usage with detected frameworks/tools into `data/tech_stack.json`. Framework detection rules are configured via `scripts/frameworks.json`.

### Prerequisites

- **Python**: 3.9+ recommended
- **Dependencies**: `requests`, `python-dotenv`
- **GitHub token**: A Personal Access Token with permission to read your repos

### Setup

- **1. Clone and enter the repo**

```bash
git clone <this-repo-url>
cd github-developer-intelligence
```

- **2. Create and activate a virtual environment (optional but recommended)**

```bash
python -m venv .venv
source .venv/bin/activate  # on macOS/Linux
# .venv\Scripts\activate   # on Windows PowerShell
```

- **3. Install dependencies**

If you have a `requirements.txt`:

```bash
pip install -r requirements.txt
```

Otherwise, install the minimal dependencies directly:

```bash
pip install requests python-dotenv
```

- **4. Configure your GitHub token**

Create a `.env` file in the project root:

```bash
echo "GITHUB_TOKEN=your_personal_access_token_here" > .env
```

Or set `GITHUB_TOKEN` in your shell environment.

### Usage

- **Step 1: Scan your repositories**

This will fetch all your repos, compute language percentages, and save the result to `data/projects.json`.

```bash
python scripts/initial_scan.py
```

- **Step 2: Detect architecture patterns**

This will read `data/projects.json`, infer high-level architectures, and save them to `data/architecture.json`.

```bash
python scripts/architecture_detector.py
```

- **Step 3: Detect tech stack (languages + frameworks/tools)**

This will read `data/projects.json`, inspect repo contents via the GitHub API to detect frameworks/tools using the rules in `scripts/frameworks.json`, and save the combined results to `data/tech_stack.json`.

```bash
python scripts/tech_stack_detector.py
```

### Extending framework detection

- To add or adjust framework/tool detection rules, edit `scripts/frameworks.json`.
- Each key is the display name of a framework/tool, and each value is an object with:
  - `file`: a filename or extension to look for in the repo root (e.g., `package.json`, `composer.json`, `.tf`).
  - `keyword`: an optional string to search for inside that file (use `null` to only check for file existence).

### Output

- **`data/projects.json`**: List of repos with language percentage breakdown and basic metadata.
- **`data/architecture.json`**: List of detected architecture pattern labels (e.g., "API Architecture", "Microservices").

### Notes

- These scripts rely on the GitHub REST API and may be subject to **rate limits** depending on your token and usage.
- The architecture detection is intentionally simple and keyword-based; you can extend `ARCH_KEYWORDS` in `scripts/architecture_detector.py` to fit your own patterns.

