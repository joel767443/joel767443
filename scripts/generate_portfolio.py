import json
from pathlib import Path
from textwrap import shorten


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
PORTFOLIO_DIR = ROOT / "portfolio"
PORTFOLIO_FILE = PORTFOLIO_DIR / "index.html"


def load_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default if default is not None else {}


def normalize_summary(proj):
    """Prefer explicit description, then summary, then fallback."""
    desc = (proj.get("description") or "").strip()
    summary = (proj.get("summary") or "").strip()

    # Clean obvious noise in summaries (markdown headings etc.)
    if summary.startswith("#"):
        # Drop markdown heading markers and take first sentence-ish
        summary = summary.lstrip("# ").split("  ", 1)[-1]

    text = desc or summary or "No README summary available."
    return shorten(text.replace("\n", " "), width=180, placeholder="…")


def format_languages(languages):
    if not languages:
        return "Unknown"
    # languages is already {lang: pct}
    top = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:4]
    return ", ".join(f"{lang} ({pct}%)" for lang, pct in top)


def build_projects_section(projects):
    # Prefer public repos first, then private
    sorted_projects = sorted(
        projects,
        key=lambda p: (p.get("private", False), p.get("name", "").lower()),
    )

    items_html = []
    for p in sorted_projects:
        name = p.get("name", "Unnamed Repo")
        url = p.get("url", "#")
        summary = normalize_summary(p)
        langs = format_languages(p.get("languages", {}))
        privacy = "Private" if p.get("private") else "Public"

        items_html.append(
            f"""
            <article class="project-card">
                <header>
                    <h3><a href="{url}" target="_blank" rel="noopener noreferrer">{name}</a></h3>
                    <span class="badge badge-{privacy.lower()}">{privacy}</span>
                </header>
                <p class="project-summary">{summary}</p>
                <p class="project-meta"><strong>Tech:</strong> {langs}</p>
            </article>
            """
        )

    return "\n".join(items_html)


def build_skill_section(tech_stack):
    if not tech_stack:
        return "<p>No tech stack data available yet.</p>"

    # Sort by percentage desc
    sorted_stack = sorted(tech_stack.items(), key=lambda x: x[1], reverse=True)

    chips = []
    for name, pct in sorted_stack:
        level = "primary" if pct >= 10 else "secondary" if pct >= 3 else "tertiary"
        chips.append(
            f'<span class="skill-chip skill-{level}" title="{pct}% of codebase">{name}</span>'
        )

    return "\n".join(chips)


def build_architecture_section(arch_data):
    if not arch_data:
        return "<p>No architecture insights computed yet.</p>"

    counts = arch_data.get("counts", {})
    total = arch_data.get("total_repos_processed") or sum(counts.values()) or 0
    if not counts:
        return "<p>No architecture patterns detected yet.</p>"

    rows = []
    for name, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total * 100) if total else 0
        rows.append(
            f"""
            <tr>
                <td>{name}</td>
                <td>{count}</td>
                <td>{pct:.1f}%</td>
            </tr>
            """
        )

    return f"""
    <p>Detected across {total} repositories.</p>
    <div class="table-wrapper">
        <table>
            <thead>
                <tr>
                    <th>Architecture</th>
                    <th>Repos</th>
                    <th>Share</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
    </div>
    """


def generate_html(projects, tech_stack, arch_data):
    projects_html = build_projects_section(projects)
    skills_html = build_skill_section(tech_stack)
    arch_html = build_architecture_section(arch_data)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Developer Portfolio – Yoweli Kachala</title>
    <style>
        :root {{
            --bg: #050816;
            --bg-alt: #0b1020;
            --card-bg: #111827;
            --accent: #22c55e;
            --accent-soft: rgba(34, 197, 94, 0.15);
            --accent-2: #38bdf8;
            --text: #f9fafb;
            --muted: #9ca3af;
            --border: #1f2937;
            --radius-lg: 16px;
            --radius-md: 10px;
            --shadow-soft: 0 22px 40px rgba(15, 23, 42, 0.85);
            --shadow-subtle: 0 12px 30px rgba(15, 23, 42, 0.6);
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif;
            background: radial-gradient(circle at top, #0f172a 0, #020617 45%, #000 100%);
            color: var(--text);
            -webkit-font-smoothing: antialiased;
        }}

        main {{
            max-width: 1120px;
            margin: 0 auto;
            padding: 40px 20px 64px;
        }}

        header.hero {{
            display: flex;
            flex-direction: column;
            gap: 18px;
            margin-bottom: 40px;
        }}

        .hero-title-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
        }}

        h1 {{
            font-size: clamp(2.4rem, 3vw, 2.8rem);
            letter-spacing: -0.04em;
            margin: 0;
        }}

        .hero-pill {{
            padding: 6px 12px;
            border-radius: 999px;
            background: linear-gradient(90deg, rgba(34, 197, 94, .14), rgba(56, 189, 248, .18));
            border: 1px solid rgba(148, 163, 184, 0.2);
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.16em;
            color: var(--muted);
            white-space: nowrap;
        }}

        .hero-subtitle {{
            max-width: 620px;
            color: var(--muted);
            font-size: 0.95rem;
            line-height: 1.6;
        }}

        .hero-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 4px;
        }}

        .meta-pill {{
            padding: 4px 10px;
            border-radius: 999px;
            border: 1px solid rgba(148, 163, 184, 0.26);
            font-size: 0.78rem;
            color: var(--muted);
            background: rgba(15, 23, 42, 0.9);
        }}

        section {{
            margin-top: 32px;
            padding: 22px 22px 20px;
            border-radius: var(--radius-lg);
            background: radial-gradient(circle at top left, rgba(56, 189, 248, 0.09), transparent 55%),
                        radial-gradient(circle at top right, rgba(34, 197, 94, 0.12), transparent 55%),
                        rgba(15, 23, 42, 0.96);
            border: 1px solid rgba(148, 163, 184, 0.18);
            box-shadow: var(--shadow-soft);
        }}

        section + section {{
            margin-top: 24px;
        }}

        section header.section-header {{
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            gap: 12px;
            margin-bottom: 18px;
        }}

        section h2 {{
            margin: 0;
            font-size: 1.1rem;
            letter-spacing: 0.09em;
            text-transform: uppercase;
            font-weight: 600;
            color: #e5e7eb;
        }}

        .section-kicker {{
            font-size: 0.78rem;
            color: var(--muted);
        }}

        .skill-grid {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}

        .skill-chip {{
            display: inline-flex;
            align-items: center;
            padding: 6px 10px;
            border-radius: 999px;
            border: 1px solid var(--border);
            font-size: 0.8rem;
            color: var(--muted);
            background: rgba(15, 23, 42, 0.98);
            backdrop-filter: blur(18px);
        }}

        .skill-primary {{
            border-color: rgba(34, 197, 94, 0.5);
            background: linear-gradient(90deg, rgba(34, 197, 94, 0.18), rgba(34, 197, 94, 0.04));
            color: #bbf7d0;
        }}

        .skill-secondary {{
            border-color: rgba(56, 189, 248, 0.42);
            background: linear-gradient(90deg, rgba(56, 189, 248, 0.16), rgba(56, 189, 248, 0.03));
            color: #e0f2fe;
        }}

        .skill-tertiary {{
            opacity: 0.9;
        }}

        .projects-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 14px;
        }}

        .project-card {{
            padding: 14px 14px 12px;
            border-radius: var(--radius-md);
            background: radial-gradient(circle at top left, rgba(56, 189, 248, 0.08), transparent 60%),
                        rgba(15, 23, 42, 0.96);
            border: 1px solid rgba(51, 65, 85, 0.85);
            box-shadow: var(--shadow-subtle);
        }}

        .project-card header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            margin-bottom: 6px;
        }}

        .project-card h3 {{
            font-size: 0.98rem;
            margin: 0;
        }}

        .project-card a {{
            color: #e5e7eb;
            text-decoration: none;
        }}

        .project-card a:hover {{
            color: var(--accent-2);
        }}

        .badge {{
            padding: 2px 8px;
            font-size: 0.7rem;
            border-radius: 999px;
            border: 1px solid rgba(148, 163, 184, 0.6);
            color: var(--muted);
            white-space: nowrap;
        }}

        .badge-public {{
            border-color: rgba(34, 197, 94, 0.8);
            color: #a7f3d0;
        }}

        .project-summary {{
            font-size: 0.86rem;
            color: var(--muted);
            margin: 4px 0 6px;
            line-height: 1.5;
        }}

        .project-meta {{
            font-size: 0.78rem;
            color: #9ca3af;
            margin: 0;
        }}

        .table-wrapper {{
            overflow-x: auto;
            margin-top: 10px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.86rem;
        }}

        th, td {{
            padding: 6px 8px;
            text-align: left;
        }}

        thead tr {{
            background: rgba(15, 23, 42, 0.96);
        }}

        tbody tr:nth-child(even) {{
            background: rgba(15, 23, 42, 0.88);
        }}

        tbody tr:nth-child(odd) {{
            background: rgba(15, 23, 42, 0.72);
        }}

        th {{
            color: #e5e7eb;
            border-bottom: 1px solid rgba(55, 65, 81, 0.9);
        }}

        td {{
            color: var(--muted);
        }}

        footer {{
            max-width: 1120px;
            margin: 0 auto;
            padding: 0 20px 40px;
            font-size: 0.78rem;
            color: var(--muted);
            display: flex;
            justify-content: space-between;
            gap: 10px;
        }}

        footer a {{
            color: var(--accent-2);
            text-decoration: none;
        }}

        footer a:hover {{
            text-decoration: underline;
        }}

        @media (max-width: 720px) {{
            main {{
                padding-top: 28px;
            }}
            section {{
                padding: 18px 16px 15px;
            }}
            .hero-title-row {{
                flex-direction: column;
                align-items: flex-start;
            }}
        }}
    </style>
</head>
<body>
    <main>
        <header class="hero">
            <div class="hero-title-row">
                <div>
                    <div class="hero-pill">AI-Augmented Software Engineer</div>
                    <h1>Yoweli Kachala</h1>
                </div>
            </div>
            <p class="hero-subtitle">
                Building AI-native systems, microservices, Laravel applications, and data-driven trading tools.
                This portfolio is generated directly from my GitHub activity to reflect how I actually ship software.
            </p>
            <div class="hero-meta">
                <span class="meta-pill">Architectures: AI-Native · ML Systems · APIs · Event-Driven</span>
                <span class="meta-pill">Back end: PHP · Laravel · Microservices</span>
                <span class="meta-pill">AI/Quant: Python · MQL5 · Automation</span>
            </div>
        </header>

        <section id="skills">
            <header class="section-header">
                <h2>TECHNICAL SKILL MAP</h2>
                <span class="section-kicker">Weighted by code volume across GitHub</span>
            </header>
            <div class="skill-grid">
                {skills_html}
            </div>
        </section>

        <section id="projects">
            <header class="section-header">
                <h2>SELECTED PROJECTS</h2>
                <span class="section-kicker">Real repositories, summarized from GitHub</span>
            </header>
            <div class="projects-grid">
                {projects_html}
            </div>
        </section>

        <section id="architecture">
            <header class="section-header">
                <h2>ARCHITECTURE FOOTPRINT</h2>
                <span class="section-kicker">Inferred patterns detected across repositories</span>
            </header>
            {arch_html}
        </section>
    </main>

    <footer>
        <span>Generated automatically by <code>github-developer-intelligence</code>.</span>
        <span>Source: <a href="https://github.com/joel767443/github-developer-intelligence" target="_blank" rel="noopener noreferrer">GitHub</a></span>
    </footer>
</body>
</html>
"""


def main():
    projects = load_json(DATA_DIR / "projects.json", default=[])
    tech_stack = load_json(DATA_DIR / "tech_stack.json", default={})
    architecture = load_json(DATA_DIR / "architecture.json", default={})

    PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)
    html = generate_html(projects, tech_stack, architecture)
    PORTFOLIO_FILE.write_text(html, encoding="utf-8")

    print(f"Portfolio written to {PORTFOLIO_FILE}")


if __name__ == "__main__":
    main()

