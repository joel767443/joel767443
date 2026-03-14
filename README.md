# GitHub Developer Intelligence

Automated pipeline that combines **GitHub repository data** and **CV extraction** to generate a developer portfolio, a personal site, and an up-to-date README—all from a single source of truth.

## What it does

- **Scans your GitHub** – Fetches public repos, READMEs, and language stats via the GitHub API.
- **Detects tech stack & architecture** – Builds language percentages and architecture patterns across repositories.
- **Extracts structured CV data** – Parses a PDF CV into JSON (experience, education, certifications, contact, first/last name).
- **Generates outputs**:
  - **Portfolio** (`portfolio/README.md`) – Markdown portfolio with skills chart image, experience, education, certifications, and public projects.
  - **Personal site** (`site/site.html`) – Styled site from `templates/site.md` with hero, skills (including skill distribution bars), experience (with bullet points), projects (formatted names, public only), and contact.
  - **README** (`README.md`) – Generated from `templates/README.template.md` with technologies, architecture summary, and featured projects.

All generated content uses the same data so your profile stays consistent across portfolio, site, and README.

## Requirements

- Python 3.8+
- [GitHub token](https://github.com/settings/tokens) (optional but recommended for higher rate limits and private repo access)

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root (see `example.env`):

```
GITHUB_TOKEN=your_github_token_here
```

## Pipeline order

Run scripts in this order to (re)build the `data/` directory and all outputs:

| Step | Script | Produces |
|------|--------|----------|
| 1 | `python scripts/initial_scan.py` | `data/projects.json` |
| 2 | `python scripts/tech_stack_detector.py` | `data/tech_stack.json` |
| 3 | `python scripts/architecture_detector.py` | `data/architecture.json` |
| 4 | `python scripts/extract_cv.py [path/to/cv.pdf]` | `data/cv_extracted.json` |
| 5 | `python scripts/generate_portfolio.py` | `portfolio/README.md`, `portfolio/skills_chart.png`, and `data/skill_categories.json` if missing |
| 6 | `python scripts/generate_site.py` | `site/site.html` |
| 7 | `python scripts/generate_readme.py` | `README.md` |

See [docs/REGENERATION.md](docs/REGENERATION.md) for the same order and notes.

## Project layout

```
├── data/                    # Generated data (git-ignored or committed per your choice)
│   ├── projects.json        # Repos from GitHub
│   ├── tech_stack.json      # Language/framework percentages
│   ├── architecture.json    # Detected architecture patterns
│   ├── cv_extracted.json    # Parsed CV (name, experience, education, certifications)
│   └── skill_categories.json
├── portfolio/               # Generated portfolio README + skills chart image
├── site/                    # Generated personal site (site.html, index.html, css/)
├── templates/
│   ├── site.md              # Site template (placeholders like {{ name }}, {{ experience_entries }})
│   └── README.template.md   # README template
├── scripts/
│   ├── initial_scan.py      # GitHub repos → projects.json
│   ├── tech_stack_detector.py
│   ├── architecture_detector.py
│   ├── extract_cv.py       # CV PDF → cv_extracted.json
│   ├── generate_portfolio.py
│   ├── generate_site.py     # Site from template + data
│   └── generate_readme.py
├── requirements.txt
└── README.md                # This file (can be overwritten by generate_readme.py)
```

## Features

- **Name handling** – CV extractor prefers “First Last”–style names over single words (e.g. place names). Portfolio and site use `first_name` + `last_name` when present so the displayed name is correct.
- **Public projects only** – Site and portfolio list only public repositories.
- **Project name formatting** – Repo names like `eugene-property-management` are shown as “Eugene Property Management”; tech keywords (e.g. PHP, JavaScript) use correct casing.
- **Skill distribution** – Site includes a bar chart of language/framework usage from `tech_stack.json`.
- **Experience as bullets** – Site experience entries show descriptions as bullet lists.

## License

Use and adapt as you like. If you reuse the scripts or templates, attribution is appreciated.
