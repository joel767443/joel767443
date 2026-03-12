## {{ name }}

**{{ title_line }}**

{{ tagline }}

---

## Snapshot

- **Total repositories analyzed**: {{ total_projects }}
- **Portfolio complexity score**: {{ complexity_score }}
- **Primary architectures**: {{ primary_architectures_line }}
- **Top languages**: {{ top_languages_line }}

---

## Technologies

{{ technologies_section }}

---

## Architecture Experience

{{ architecture_paragraph }}

{{ architecture_list }}

---

## Featured Projects

{{ featured_projects_section }}

---

## All Scanned Repositories

{{ all_projects_section }}

---

## Skill Graph

![Skills](graphs/skills_chart.png)

{{ skills_caption }}

---

## How This README Is Generated

This README is generated automatically from:

- `data/projects.json` (per-repo metadata, languages, and summaries)
- `data/tech_stack.json` (global technology usage)
- `data/architecture.json` (detected architecture patterns)
- `reports/capability_report.txt` (high-level capability report)

Run the generator to refresh the data and regenerate this file after rescanning your GitHub repositories.

