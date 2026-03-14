import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

_script_dir = Path(__file__).resolve().parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))
from common import ROOT, DATA_DIR, TEMPLATES_DIR, REPORTS_DIR, load_json, render_template


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
            lines.append(f"- **[{name}]({url})** – {langs}")
        else:
            lines.append(f"- **{name}** – {langs}")
        lines.append(f"  {desc}")
    return "\n".join(lines)


def main() -> None:
    projects_path = DATA_DIR / "projects.json"
    tech_stack_path = DATA_DIR / "tech_stack.json"
    arch_path = DATA_DIR / "architecture.json"
    capability_report_path = REPORTS_DIR / "capability_report.txt"
    template_path = TEMPLATES_DIR / "README.template.md"
    output_readme_path = ROOT / "README.md"

    projects = load_json(projects_path, default=None) or []
    tech_stack = load_json(tech_stack_path, default=None) or {}
    architecture = load_json(arch_path, default=None) or {}
    total_projects_report, complexity_score = load_capability_report(capability_report_path)

    # Fallback for total projects if capability report is missing
    if not total_projects_report and projects:
        total_projects_report = len(projects)

    tech_section = build_technologies_section(tech_stack)
    arch_paragraph, arch_list, primary_arch_line = build_architecture_summaries(architecture or {})
    featured_section = build_featured_projects_section(projects)
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

    # Build recruiter- and founder-friendly narrative pieces
    total_repos = total_projects_report or len(projects)
    hero_paragraph = (
        "Senior systems architect and full stack engineer focused on AI-native products, "
        "trading and quantitative tools, and scalable SaaS platforms."
    )
    hero_value_bullets = (
        "- **AI & trading systems**: Python/MQL5 engines, backtesting, and automation.\n"
        "- **Scalable APIs & backends**: PHP/Laravel, microservices, Docker-based deployments.\n"
        "- **End-to-end product delivery**: from prototype to production across web, mobile, and cloud."
    )

    what_im_looking_for_section = (
        "- Senior backend or full stack roles building AI-powered products or data-heavy systems.\n"
        "- Early engineering hire or founding engineer roles at product-focused startups.\n"
        "- Positions where I own architecture decisions and help teams ship reliably to production."
    )

    counts = architecture.get("counts", {}) if architecture else {}
    ml_count = counts.get("Machine Learning Systems", 0)
    api_count = counts.get("API Architecture", 0)
    micro_count = counts.get("Microservices", 0)
    impact_lines = [
        f"- Designed and maintained AI/ML and quantitative trading projects across **{ml_count}** repositories."
        if ml_count
        else "- Designed and maintained multiple AI/ML and quantitative trading projects.",
        f"- Built and integrated REST-style APIs and backend services in **{api_count}**+ codebases using PHP/Laravel, Python, and JavaScript."
        if api_count
        else "- Built and integrated REST-style APIs and backend services using PHP/Laravel, Python, and JavaScript.",
        f"- Applied service-oriented and microservice patterns in **{micro_count}** projects with Dockerized deployments."
        if micro_count
        else "- Applied service-oriented and microservice patterns with Dockerized deployments.",
        f"- Curated and actively maintain a portfolio of **{total_repos}** repositories that showcase production-grade code, automation, and CI/CD."
        if total_repos
        else "- Maintain a portfolio of repositories that showcase production-grade code, automation, and CI/CD.",
    ]
    impact_highlights_section = "\n".join(impact_lines)

    snapshot_intro = (
        "These metrics are derived automatically from my GitHub activity and give a quick view "
        "of where I spend most of my time."
    )
    technologies_intro = (
        "Heavier percentages indicate where I have the deepest hands-on experience; "
        "PHP, Python, and Swift are my most-used languages."
    )
    architecture_intro = (
        "I design and work with architectures that support real-world constraints like latency, "
        "throughput, and iterative delivery across ML systems, APIs, and microservices."
    )
    generation_note = (
        "This portfolio is generated from my GitHub repositories using custom Python tooling "
        "in the `scripts/` folder, combining language stats, architecture detection, and project summaries."
    )

    context = {
        "name": "Yoweli Kachala",
        "title_line": "Senior Systems Architect • Full Stack Engineer",
        "hero_paragraph": hero_paragraph,
        "hero_value_bullets": hero_value_bullets,
        "what_im_looking_for_section": what_im_looking_for_section,
        "impact_highlights_section": impact_highlights_section,
        "total_projects": str(total_projects_report),
        "primary_architectures_line": primary_arch_line or "Not enough architecture data yet.",
        "top_languages_line": top_langs_line,
        "snapshot_intro": snapshot_intro,
        "technologies_intro": technologies_intro,
        "technologies_section": tech_section,
        "architecture_intro": architecture_intro,
        "architecture_paragraph": arch_paragraph,
        "architecture_list": arch_list,
        "skills_caption": skills_caption,
        "generation_note": generation_note,
        "featured_projects_section": featured_section,
    }

    rendered = render_template(template, context)
    with output_readme_path.open("w", encoding="utf-8") as f:
        f.write(rendered)

    print(f"README generated at {output_readme_path}")


if __name__ == "__main__":
    main()

