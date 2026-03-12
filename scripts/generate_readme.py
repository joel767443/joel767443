import json
from pathlib import Path
from typing import List, Dict, Any, Tuple


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"
TEMPLATES_DIR = ROOT / "templates"


def load_json(path: Path) -> Any:
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_capability_report(path: Path) -> Tuple[int, int]:
    """
    Returns (total_projects, complexity_score) from capability_report.txt.
    Falls back to (0, 0) if not found/parsable.
    """
    total_projects = 0
    complexity_score = 0
    if not path.exists():
        return total_projects, complexity_score

    try:
        with path.open(encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines()]
    except OSError:
        return total_projects, complexity_score

    for idx, line in enumerate(lines):
        if line.startswith("Total Projects:"):
            try:
                total_projects = int(line.split(":", 1)[1].strip())
            except ValueError:
                pass
        if line.startswith("Estimated Complexity Score:") or line.startswith("Estimated Complexity Score"):
            # Line may be split on the next line in the file
            if ":" in line:
                try:
                    complexity_score = int(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
            else:
                if idx + 1 < len(lines):
                    nxt = lines[idx + 1].strip()
                    if nxt.isdigit():
                        complexity_score = int(nxt)
    return total_projects, complexity_score


def format_top_languages(stack: Dict[str, float], limit: int = 5) -> str:
    if not stack:
        return "Not enough data yet."
    items = sorted(stack.items(), key=lambda x: x[1], reverse=True)[:limit]
    return ", ".join(f"{name} ({pct}%)" for name, pct in items)


def build_technologies_section(stack: Dict[str, float]) -> str:
    if not stack:
        return "_No technologies detected yet._"

    lines = ["| Technology | Usage |", "|-----------|-------|"]
    for name, pct in sorted(stack.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"| {name} | {pct}% |")
    return "\n".join(lines)


def build_architecture_summaries(arch: Dict[str, Any]) -> Tuple[str, str, str]:
    if not arch:
        return (
            "Architecture patterns will appear here once repositories have been analyzed.",
            "",
            "",
        )

    counts = arch.get("counts", {})
    total = arch.get("total_repos_processed") or sum(counts.values()) or 0
    if not counts:
        return (
            "Architecture patterns will appear here once repositories have been analyzed.",
            "",
            "",
        )

    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    # Paragraph
    top_names = [name for name, _ in sorted_counts[:3]]
    paragraph = (
        f"Across {total} repositories, recurring architecture patterns include "
        + ", ".join(top_names)
        + "."
    )

    # Bullet list
    bullet_lines = []
    for name, count in sorted_counts:
        bullet_lines.append(f"- **{name}**: {count} repos")
    bullet_block = "\n".join(bullet_lines)

    # Single-line summary for snapshot
    primary_line = ", ".join(f"{name} ({count})" for name, count in sorted_counts[:3])

    return paragraph, bullet_block, primary_line


def pick_featured_projects(projects: List[Dict[str, Any]], limit: int = 6) -> List[Dict[str, Any]]:
    if not projects:
        return []

    # Prefer public repos, then sort by whether they have a non-empty summary/description
    def project_key(p: Dict[str, Any]):
        private = p.get("private", False)
        has_summary = bool(p.get("summary"))
        has_description = bool(p.get("description"))
        return (
            private,                  # public first (False < True)
            not (has_summary or has_description),  # ones with content first
        )

    sorted_projects = sorted(projects, key=project_key)
    return sorted_projects[:limit]


def languages_summary(languages: Dict[str, float], limit: int = 3) -> str:
    if not languages:
        return "Languages: N/A"
    items = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:limit]
    return "Languages: " + ", ".join(f"{name} ({pct}%)" for name, pct in items)


def build_featured_projects_section(projects: List[Dict[str, Any]]) -> str:
    if not projects:
        return "_No projects available yet._"

    featured = pick_featured_projects(projects)
    lines: List[str] = []
    for p in featured:
        name = p.get("name", "Unnamed")
        url = p.get("url", "")
        desc = p.get("description") or p.get("summary") or "Summary not available yet."
        langs = languages_summary(p.get("languages", {}))

        if url:
            lines.append(f"- **[{name}]({url})**  ")
        else:
            lines.append(f"- **{name}**  ")
        lines.append(f"  {langs}  ")
        lines.append(f"  {desc}")
    return "\n".join(lines)


def build_all_projects_section(projects: List[Dict[str, Any]]) -> str:
    if not projects:
        return "_No repositories found._"
    lines = []
    for p in projects:
        name = p.get("name", "Unnamed")
        url = p.get("url", "")
        if url:
            lines.append(f"- [{name}]({url})")
        else:
            lines.append(f"- {name}")
    return "\n".join(lines)


def render_template(template: str, context: Dict[str, str]) -> str:
    # Very simple placeholder replacement: {{ key }}
    result = template
    for key, value in context.items():
        placeholder = "{{ " + key + " }}"
        result = result.replace(placeholder, value)
    return result


def main() -> None:
    projects_path = DATA_DIR / "projects.json"
    tech_stack_path = DATA_DIR / "tech_stack.json"
    arch_path = DATA_DIR / "architecture.json"
    capability_report_path = REPORTS_DIR / "capability_report.txt"
    template_path = TEMPLATES_DIR / "README.template.md"
    output_readme_path = ROOT / "README.md"

    projects = load_json(projects_path) or []
    tech_stack = load_json(tech_stack_path) or {}
    architecture = load_json(arch_path) or {}
    total_projects_report, complexity_score = load_capability_report(capability_report_path)

    # Fallback for total projects if capability report is missing
    if not total_projects_report and projects:
        total_projects_report = len(projects)

    tech_section = build_technologies_section(tech_stack)
    arch_paragraph, arch_list, primary_arch_line = build_architecture_summaries(architecture or {})
    featured_section = build_featured_projects_section(projects)
    all_projects_section = build_all_projects_section(projects)
    top_langs_line = format_top_languages(tech_stack)

    # Simple caption for skills graph
    if tech_stack:
        top_langs_names = ", ".join(
            name for name, _ in sorted(tech_stack.items(), key=lambda x: x[1], reverse=True)[:3]
        )
        skills_caption = f"_Skill graph highlighting strongest technologies: {top_langs_names}._"
    else:
        skills_caption = ""

    if not template_path.exists():
        raise SystemExit(f"Template not found at {template_path}")

    with template_path.open(encoding="utf-8") as f:
        template = f.read()

    context = {
        "name": "Yoweli Kachala",
        "title_line": "Senior Systems Architect • Full Stack Engineer",
        "tagline": "Designing and shipping AI-native systems, distributed backends, and production-ready trading infrastructure across web, mobile, and cloud.",
        "total_projects": str(total_projects_report),
        "complexity_score": str(complexity_score) if complexity_score else "N/A",
        "primary_architectures_line": primary_arch_line or "Not enough architecture data yet.",
        "top_languages_line": top_langs_line,
        "technologies_section": tech_section,
        "architecture_paragraph": arch_paragraph,
        "architecture_list": arch_list,
        "featured_projects_section": featured_section,
        "all_projects_section": all_projects_section,
        "skills_caption": skills_caption,
    }

    rendered = render_template(template, context)
    with output_readme_path.open("w", encoding="utf-8") as f:
        f.write(rendered)

    print(f"README generated at {output_readme_path}")


if __name__ == "__main__":
    main()

