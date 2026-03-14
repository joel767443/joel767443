import json
from pathlib import Path
from textwrap import shorten

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
PORTFOLIO_DIR = ROOT / "portfolio"
PORTFOLIO_FILE = PORTFOLIO_DIR / "index.html"

# Map tech_stack keys to CV skill categories (Languages, Tools, Frontend, Backend, Backend as a service)
SKILL_CATEGORIES = {
    "languages": {
        "PHP", "Python", "Swift", "Java", "JavaScript", "TypeScript", "HTML", "CSS",
        "MQL5", "Hack", "C++", "Shell", "PowerShell", "SCSS", "Less", "Roff", "Blade",
    },
    "tools": {
        "Docker", "Dockerfile", "Vite", "Makefile", "Terraform", "Ansible", "CMake",
        "Batchfile", "Git", "Github",
    },
    "frontend": {
        "Vue", "React", "Tailwind CSS", "Svelte", "SvelteKit", "Astro", "Solid.js",
        "Qwik", "Remix", "Next.js", "Nuxt.js", "Angular",
    },
    "backend": {
        "Laravel", "Symfony", "Django", "Flask", "FastAPI", "Express", "NestJS",
        "Rails", "Sinatra", "Spring Boot", "Quarkus", "ASP.NET Core", "Gin", "Hono",
        "Tornado", "Pyramid", "Yii", "CodeIgniter", "CakePHP", "Zend", "Phalcon",
        "Prisma", "Bun",
    },
    "backend_services": {
        "Supabase", "PostgreSQL", "MySQL", "Redis", "Kubernetes", "AWS",
    },
}


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


def _skill_category(name):
    """Return category key for a tech name, or 'other'."""
    for cat, keys in SKILL_CATEGORIES.items():
        if name in keys:
            return cat
    return "other"


def build_projects_section(projects):
    # Projects are already filtered to public; sort by name
    sorted_projects = sorted(projects, key=lambda p: p.get("name", "").lower())

    items_html = []
    for p in sorted_projects:
        name = p.get("name", "Unnamed Repo")
        url = p.get("url", "#")
        summary = normalize_summary(p)
        langs = format_languages(p.get("languages", {}))

        items_html.append(
            f"""
            <article class="project-card">
                <header>
                    <h3><a href="{url}" target="_blank" rel="noopener noreferrer">{name}</a></h3>
                    <span class="badge badge-public">Public</span>
                </header>
                <p class="project-summary">{summary}</p>
                <p class="project-meta"><strong>Tech:</strong> {langs}</p>
            </article>
            """
        )

    return "\n".join(items_html)


def build_technical_skills_grouped(tech_stack):
    """Build Technical skills section with subsections: Languages, Tools, Frontend, Backend, Backend as a service, Other."""
    if not tech_stack:
        return "<p>No tech stack data available yet.</p>"

    sorted_stack = sorted(tech_stack.items(), key=lambda x: x[1], reverse=True)
    category_labels = {
        "languages": "Languages",
        "tools": "Tools",
        "frontend": "Frontend libraries and frameworks",
        "backend": "Backend libraries and frameworks",
        "backend_services": "Backend as a service / Services",
        "other": "Other",
    }
    grouped = {cat: [] for cat in category_labels}
    for name, pct in sorted_stack:
        cat = _skill_category(name)
        level = "primary" if pct >= 10 else "secondary" if pct >= 3 else "tertiary"
        grouped[cat].append((name, pct, level))

    parts = []
    for cat_key, label in category_labels.items():
        items = grouped.get(cat_key) or []
        if not items:
            continue
        chips = " ".join(
            f'<span class="skill-chip skill-{level}" title="{pct}%">{name}</span>'
            for name, pct, level in items
        )
        parts.append(
            f'<div class="skill-group"><h3 class="skill-group-title">{label}</h3>'
            f'<div class="skill-grid">{chips}</div></div>'
        )
    if not parts:
        return "<p>No tech stack data available yet.</p>"
    return "\n".join(parts)


def build_experience_section(cv_data):
    """Build Professional experience from CV experience list (flat list of strings)."""
    experience = cv_data.get("experience") or []
    if not experience:
        return "<p>No experience data.</p>"
    # Render as list of items; pyresparser gives flat list (company, title, dates, location, bullets)
    lines = []
    for i, item in enumerate(experience):
        s = (item or "").strip()
        if not s or s.startswith("Page "):
            continue
        lines.append(f"<li class=\"cv-item\">{s}</li>")
    if not lines:
        return "<p>No experience data.</p>"
    return "<ul class=\"cv-list\">" + "".join(lines) + "</ul>"


def build_education_section(cv_data):
    """Build Education from CV degree and college_name."""
    degree = cv_data.get("degree") or []
    college = cv_data.get("college_name")
    if isinstance(degree, str):
        degree = [degree] if degree else []
    if not degree and not college:
        return "<p>No education data.</p>"
    lines = []
    if college:
        lines.append(f"<li class=\"cv-item\">{college}</li>")
    for d in degree:
        if d and str(d).strip():
            lines.append(f"<li class=\"cv-item\">{d}</li>")
    if not lines:
        return "<p>No education data.</p>"
    return "<ul class=\"cv-list\">" + "".join(lines) + "</ul>"


def build_certifications_section(cv_data):
    """Build Certifications from CV certifications key if present."""
    certs = cv_data.get("certifications")
    if certs is None:
        certs = []
    if isinstance(certs, str) and certs.strip():
        certs = [certs]
    if not certs:
        return "<p>None listed.</p>"
    lines = [f"<li class=\"cv-item\">{c}</li>" for c in certs if c and str(c).strip()]
    if not lines:
        return "<p>None listed.</p>"
    return "<ul class=\"cv-list\">" + "".join(lines) + "</ul>"


def generate_skills_chart(tech_stack, arch_data, output_path):
    """Generate skills + architecture bar chart and save to output_path (e.g. portfolio/skills_chart.png)."""
    skill_names = list(tech_stack.keys()) if tech_stack else []
    skill_values = list(tech_stack.values()) if tech_stack else []
    arch_counts = (arch_data or {}).get("counts", {})
    arch_names = list(arch_counts.keys())
    arch_values = list(arch_counts.values())
    has_arch = bool(arch_counts)

    if has_arch:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    else:
        fig, ax1 = plt.subplots(1, 1, figsize=(10, 4))

    if skill_names:
        ax1.bar(skill_names, skill_values, color=(0.13, 0.77, 0.37, 0.85))
        ax1.set_title("Developer Skill Distribution")
        ax1.set_xticks(range(len(skill_names)))
        ax1.set_xticklabels(skill_names, rotation=45, ha="right")
        ax1.set_facecolor((0.06, 0.09, 0.16, 0.98))
        ax1.tick_params(colors="#9ca3af")
        ax1.spines["bottom"].set_color("#374151")
        ax1.spines["left"].set_color("#374151")
    if has_arch:
        ax2.bar(arch_names, arch_values, color=(0.22, 0.74, 0.97, 0.85))
        ax2.set_title("Detected Architectures Across Repositories")
        ax2.set_xticks(range(len(arch_names)))
        ax2.set_xticklabels(arch_names, rotation=45, ha="right")
        ax2.set_facecolor((0.06, 0.09, 0.16, 0.98))
        ax2.tick_params(colors="#9ca3af")
        ax2.spines["bottom"].set_color("#374151")
        ax2.spines["left"].set_color("#374151")

    fig.patch.set_facecolor((0.06, 0.09, 0.16, 0.98))
    fig.tight_layout()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)


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


def generate_html(projects, tech_stack, arch_data, cv_data):
    projects_html = build_projects_section(projects)
    skills_grouped_html = build_technical_skills_grouped(tech_stack)
    arch_html = build_architecture_section(arch_data)
    experience_html = build_experience_section(cv_data)
    education_html = build_education_section(cv_data)
    certifications_html = build_certifications_section(cv_data)
    hero_name = (cv_data.get("name") or "Yoweli Kachala").strip() or "Yoweli Kachala"

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

        .skill-group {{
            margin-bottom: 20px;
        }}

        .skill-group:last-child {{
            margin-bottom: 0;
        }}

        .skill-group-title {{
            font-size: 0.9rem;
            font-weight: 600;
            color: #d1d5db;
            margin: 0 0 8px 0;
            letter-spacing: 0.05em;
        }}

        .cv-list {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}

        .cv-item {{
            font-size: 0.9rem;
            color: var(--muted);
            line-height: 1.55;
            padding: 6px 0;
            border-bottom: 1px solid rgba(55, 65, 81, 0.5);
        }}

        .cv-item:last-child {{
            border-bottom: none;
        }}

        #skills-graph img {{
            max-width: 100%;
            height: auto;
            border-radius: var(--radius-md);
            border: 1px solid rgba(55, 65, 85, 0.85);
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
                    <h1>{hero_name}</h1>
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
                <h2>Technical skills</h2>
                <span class="section-kicker">Weighted by code volume across GitHub</span>
            </header>
            {skills_grouped_html}
        </section>

        <section id="skills-graph">
            <header class="section-header">
                <h2>Skill distribution</h2>
                <span class="section-kicker">Languages and architectures</span>
            </header>
            <img src="skills_chart.png" alt="Skills and architectures" />
        </section>

        <section id="experience">
            <header class="section-header">
                <h2>Professional experience</h2>
            </header>
            {experience_html}
        </section>

        <section id="education">
            <header class="section-header">
                <h2>Education</h2>
            </header>
            {education_html}
        </section>

        <section id="certifications">
            <header class="section-header">
                <h2>Certifications</h2>
            </header>
            {certifications_html}
        </section>

        <section id="projects">
            <header class="section-header">
                <h2>Featured Projects</h2>
                <span class="section-kicker">Public repositories, summarized from GitHub</span>
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
    projects = [p for p in projects if not p.get("private", True)]
    tech_stack = load_json(DATA_DIR / "tech_stack.json", default={})
    architecture = load_json(DATA_DIR / "architecture.json", default={})
    cv_data = load_json(DATA_DIR / "cv_extracted.json", default={})

    PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)
    generate_skills_chart(tech_stack, architecture, PORTFOLIO_DIR / "skills_chart.png")
    html = generate_html(projects, tech_stack, architecture, cv_data)
    PORTFOLIO_FILE.write_text(html, encoding="utf-8")

    print(f"Portfolio written to {PORTFOLIO_FILE}")


if __name__ == "__main__":
    main()

