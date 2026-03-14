#!/usr/bin/env python3
"""
Generate site/site.html from templates/site.md by replacing placeholders
with data from data/cv_extracted.json, data/skill_categories.json, and optional
data/tech_stack.json and data/projects.json. Output matches site/index.html
structure so css/styles.css applies the same design.
"""

import html as html_module
import json
import sys
from pathlib import Path
from textwrap import shorten

_script_dir = Path(__file__).resolve().parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))
from common import ROOT, DATA_DIR, TEMPLATES_DIR, SITE_DIR, load_json, render_template, get_display_name

SITE_TEMPLATE = TEMPLATES_DIR / "site.md"
OUTPUT_HTML = SITE_DIR / "site.html"


# --- HTML builders (match site/index.html structure and classes) ---

def _e(s: str) -> str:
    """Escape for HTML text content."""
    return html_module.escape(s) if s else ""


# Canonical casing for tech/product keywords (lowercase key -> display form)
TECH_KEYWORDS = {
    "php": "PHP",
    "html": "HTML",
    "css": "CSS",
    "sql": "SQL",
    "json": "JSON",
    "xml": "XML",
    "api": "API",
    "rest": "REST",
    "graphql": "GraphQL",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "node": "Node.js",
    "nodejs": "Node.js",
    "react": "React",
    "vue": "Vue",
    "angular": "Angular",
    "nextjs": "Next.js",
    "nuxt": "Nuxt",
    "laravel": "Laravel",
    "django": "Django",
    "rails": "Rails",
    "express": "Express",
    "fastapi": "FastAPI",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "terraform": "Terraform",
    "aws": "AWS",
    "gcp": "GCP",
    "ios": "iOS",
    "android": "Android",
    "swift": "Swift",
    "kotlin": "Kotlin",
    "python": "Python",
    "java": "Java",
    "csharp": "C#",
    "c++": "C++",
    "go": "Go",
    "rust": "Rust",
    "redis": "Redis",
    "mongodb": "MongoDB",
    "postgresql": "PostgreSQL",
    "mysql": "MySQL",
    "github": "GitHub",
    "gitlab": "GitLab",
    "figma": "Figma",
    "vite": "Vite",
    "webpack": "Webpack",
    "jest": "Jest",
    "cypress": "Cypress",
}


def format_project_name(raw: str) -> str:
    """Convert repo-style names to display format: eugene-property-management -> Eugene Property Management.
    Uses TECH_KEYWORDS so e.g. Php -> PHP, Javascript -> JavaScript.
    """
    if not raw or not raw.strip():
        return raw
    s = raw.strip()
    for sep in ("-", "_", "."):
        s = s.replace(sep, " ")
    parts = s.split()
    result = []
    for p in parts:
        if not p:
            continue
        key = p.lower()
        if key in TECH_KEYWORDS:
            result.append(TECH_KEYWORDS[key])
        elif p.isupper() and len(p) > 1:
            result.append(p)  # Keep README, etc.
        else:
            result.append(p[0].upper() + p[1:].lower() if len(p) > 1 else p.upper())
    return " ".join(result)


def build_hero_html(ctx: dict) -> str:
    name = _e(ctx["name"])
    title = _e(ctx["title"])
    headline = _e(ctx.get("headline") or ctx["title"])
    experience_summary = _e(ctx["experience_summary"])
    tagline = _e(ctx["tagline"])
    resume_url = _e(ctx["resume_url"])
    github_url = _e(ctx["github_url"])
    linkedin_url = _e(ctx["linkedin_url"])
    image_url = _e(ctx["image_url"])
    return f"""  <section id="home" class="section hero">
  <div class="hero-bg"></div>
  <div class="hero-inner container">
    <div class="hero-content">
      <h1 class="hero-title">
        <span></span>
        <span class="hero-name">{name}</span>
      </h1>
      <p class="hero-headline">{headline}</p>
      <p class="hero-subtitle">
        <span class="highlight">{_e(ctx.get("highlight_years", "5+ years"))}</span>
        of expertise.
      </p>
      <p class="hero-description">
        {tagline}
      </p>
      <div class="hero-actions">
        <a href="{resume_url}" target="_blank" class="btn btn-primary">Download Resume</a>
        <a href="#projects" class="btn btn-outline">View My Work</a>
      </div>
      <div class="hero-social">
        <a href="{github_url}" aria-label="GitHub" class="icon-button">GH</a>
        <a href="{linkedin_url}" aria-label="LinkedIn" class="icon-button">in</a>
        <a href="#contact" aria-label="Email" class="icon-button">@</a>
      </div>
    </div>
    <div class="hero-image-wrapper">
      <div class="hero-image-glow"></div>
      <div class="hero-image-card">
        <img src="{image_url}" alt="{name} - {title}" />
        <div class="hero-availability">
          <span class="dot"></span>
          Available for hire
        </div>
      </div>
    </div>
  </div>
</section>
"""


def build_skill_distribution_html(tech_stack: dict) -> str:
    """Build a horizontal bar chart of skill usage (from tech_stack percentages)."""
    if not tech_stack:
        return ""
    sorted_stack = sorted(tech_stack.items(), key=lambda x: x[1], reverse=True)[:16]
    max_pct = max((pct for _, pct in sorted_stack), default=100)
    bars = []
    for skill_name, pct in sorted_stack:
        width = (pct / max_pct * 100) if max_pct else 0
        bars.append(f"""    <div class="skill-distribution-row">
      <span class="skill-distribution-label">{_e(skill_name)}</span>
      <div class="skill-distribution-bar-wrap">
        <div class="skill-distribution-bar" style="width: {width:.0f}%"></div>
      </div>
      <span class="skill-distribution-pct">{pct:.1f}%</span>
    </div>""")
    return """
    <header class="section-header" style="margin-top: 3rem;">
      <h2>Skill Distribution</h2>
      <p>Language and framework usage across public repositories (by code percentage).</p>
    </header>
    <div class="skill-distribution">
""" + "\n".join(bars) + """
    </div>
"""


def _skills_for_category(skill_categories: dict, tech_stack: dict, key: str) -> list:
    cat = skill_categories.get(key)
    if not cat:
        return []
    items = cat.get("items") or []
    if tech_stack:
        items = [i for i in items if i in tech_stack]
    return items


def build_skills_html(skill_categories: dict, tech_stack: dict) -> str:
    # Match index.html: Programming Languages, DevOps & Tools, JavaScript Libraries & Frameworks, Web Frameworks, Backend as a Service, Testing
    groups = [
        ("languages", "Programming Languages"),
        ("tools", "DevOps & Tools"),
        ("frontend", "JavaScript Libraries & Frameworks"),
        ("backend", "Web Frameworks"),
        ("backend_services", "Backend as a Service"),
    ]
    cards = []
    for cat_key, label in groups:
        items = _skills_for_category(skill_categories, tech_stack, cat_key)
        if not items and cat_key == "backend_services":
            items = ["Firebase", "Appwrite"]  # fallback so section isn’t empty
        badges = "".join(f'<span class="badge">{_e(s)}</span>' for s in items)
        cards.append(f"""      <article class="card">
          <h3 class="card-title">{_e(label)}</h3>
          <div class="badges">{badges or '<span class="badge">—</span>'}</div>
        </article>""")
    # Testing (no category in skill_categories)
    cards.append("""      <article class="card">
          <h3 class="card-title">Testing</h3>
          <div class="badges"><span class="badge">Jest</span></div>
        </article>""")

    # Skill distribution (bar chart from tech_stack)
    distribution_html = build_skill_distribution_html(tech_stack)

    return f"""  <section id="skills" class="section section-alt">
  <div class="container">
    <header class="section-header">
      <h2>Technical Skills</h2>
      <p>
        Comprehensive expertise across modern development stack with focus on scalable web applications and DevOps practices.
      </p>
    </header>

    <div class="grid skills-grid">
{chr(10).join(cards)}
    </div>
{distribution_html}
  </div>
</section>
"""


def build_experience_html(cv_data: dict) -> str:
    entries = cv_data.get("experience_entries") or []
    if not entries or not isinstance(entries[0], dict):
        return ""
    blocks = []
    for e in entries:
        title = (e.get("title") or "").strip()
        company = (e.get("company") or "").strip()
        dates = (e.get("dates") or "").strip()
        loc = (e.get("location") or "").strip()
        if not title and not company:
            continue
        desc = e.get("description")
        if isinstance(desc, list):
            bullets = [str(b).strip() for b in desc if b and str(b).strip()]
        elif desc and str(desc).strip():
            bullets = [s.strip() + "." for s in str(desc).split(". ") if s.strip()]
            if bullets and not bullets[-1].endswith("."):
                bullets[-1] = bullets[-1] + "."
        else:
            bullets = []
        skills = e.get("skills") or []
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(",") if s.strip()]
        tags = "".join(f'<span class="badge badge-outline">{_e(s)}</span>' for s in skills)
        if bullets:
            desc_html = "<ul class=\"muted exp-bullets\">" + "".join(f"<li>{_e(b)}</li>" for b in bullets) + "</ul>"
        else:
            desc_html = ""
        blocks.append(f"""      <article class="card">
          <div class="experience-header">
            <div>
              <h3>{_e(title or "—")}</h3>
              <p class="accent">{_e(company or "—")}</p>
            </div>
            <div class="experience-meta">
              <span>{_e(dates)}</span>
              <span>{_e(loc)}</span>
            </div>
          </div>
          {desc_html}
          <div class="badges">{tags}</div>
        </article>""")
    if not blocks:
        return ""
    return "\n".join(blocks)


def build_education_html(cv_data: dict) -> str:
    education = cv_data.get("education") or []
    if not education and isinstance(cv_data.get("degree"), list):
        degree = cv_data.get("degree") or []
        college = (cv_data.get("college_name") or "").strip()
        if isinstance(degree, str):
            degree = [degree] if degree else []
        education = [{"degree": (d or "").strip(), "institution": college, "dates": "", "location": ""} for d in degree if d and str(d).strip()]
        if not education and college:
            education = [{"degree": "", "institution": college, "dates": "", "location": ""}]
    if not education:
        return ""
    blocks = []
    for e in education:
        if not isinstance(e, dict):
            continue
        degree_title = (e.get("degree") or "").strip()
        institution = (e.get("institution") or "").strip()
        dates = (e.get("dates") or "").strip()
        loc = (e.get("location") or "").strip()
        if not degree_title and not institution:
            continue
        blocks.append(f"""      <article class="card">
          <div class="experience-header">
            <div>
              <h3>{_e(degree_title or "—")}</h3>
              <p class="accent">{_e(institution or "—")}</p>
            </div>
            <div class="experience-meta">
              <span>{_e(dates)}</span>
              <span>{_e(loc)}</span>
            </div>
          </div>
        </article>""")
    return "\n".join(blocks)


def build_certifications_html(cv_data: dict) -> str:
    certs = cv_data.get("certifications") or []
    if isinstance(certs, str) and certs.strip():
        certs = [certs]
    if not certs:
        return ""
    blocks = []
    for c in certs:
        if isinstance(c, dict):
            name = (c.get("name") or "").strip()
            issuer = (c.get("issuer") or "").strip()
            if not name and not issuer:
                continue
            blocks.append(f"""      <article class="card">
          <div class="experience-header">
            <div>
              <h3>{_e(name or "—")}</h3>
              <p class="accent">{_e(issuer or "—")}</p>
            </div>
          </div>
        </article>""")
        elif c and str(c).strip():
            blocks.append(f"""      <article class="card">
          <div class="experience-header">
            <div>
              <h3>{_e(str(c).strip())}</h3>
            </div>
          </div>
        </article>""")
    return "\n".join(blocks)


def build_projects_html(projects: list) -> str:
    if not projects:
        return ""
    from textwrap import shorten as sh
    default_img = "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=600&h=400&fit=crop"
    blocks = []
    for p in sorted(projects, key=lambda x: (x.get("name") or "").lower())[:12]:
        raw_name = p.get("name") or "Unnamed"
        display_name = format_project_name(raw_name)
        url = p.get("url") or "#"
        desc = (p.get("description") or p.get("summary") or "").strip()
        if desc and desc.startswith("#"):
            desc = desc.lstrip("# ").split("  ", 1)[-1]
        desc = sh(desc.replace("\n", " "), width=200, placeholder="…") if desc else "No description."
        langs = p.get("languages") or {}
        top = sorted(langs.items(), key=lambda x: x[1], reverse=True)[:5]
        badges = "".join(f'<span class="badge">{_e(lang)}</span>' for lang, _ in top) if top else ""
        img = p.get("image_url") or default_img
        blocks.append(f"""      <article class="card project-card">
          <div class="project-image">
            <img src="{_e(img)}" alt="{_e(display_name)}" />
          </div>
          <div class="project-body">
            <h3><a href="{_e(url)}" target="_blank" rel="noopener noreferrer">{_e(display_name)}</a></h3>
            <p class="muted">{_e(desc)}</p>
            <div class="badges">{badges}</div>
          </div>
        </article>""")
    return "\n".join(blocks)


def build_contact_html(ctx: dict) -> str:
    email = _e(ctx["email"])
    phone = _e(ctx["phone"])
    location = _e(ctx["location"])
    return f"""    <div class="grid contact-grid">
      <div class="contact-details">
        <article class="card">
          <div class="contact-item">
            <h3>Email</h3>
            <p class="muted">{email}</p>
          </div>
        </article>
        <article class="card">
          <div class="contact-item">
            <h3>Phone</h3>
            <p class="muted">{phone}</p>
          </div>
        </article>
        <article class="card">
          <div class="contact-item">
            <h3>Location</h3>
            <p class="muted">{location}</p>
          </div>
        </article>
      </div>

      <article class="card contact-form-card">
        <h3>Send a Message</h3>
        <form class="contact-form" novalidate>
          <div class="form-row">
            <input type="text" name="name" placeholder="Your Name" />
            <input type="email" name="email" placeholder="Your Email" />
          </div>
          <input type="text" name="subject" placeholder="Subject" />
          <textarea name="message" rows="5" placeholder="Your Message"></textarea>
          <button type="submit" class="btn btn-primary btn-full">
            Send Message
          </button>
        </form>
      </article>
    </div>
"""


def main() -> None:
    cv_data = load_json(DATA_DIR / "cv_extracted.json", default={}) or {}
    skill_categories = load_json(DATA_DIR / "skill_categories.json", default={}) or {}
    tech_stack = load_json(DATA_DIR / "tech_stack.json", default={}) or {}
    projects = load_json(DATA_DIR / "projects.json", default=[]) or []
    projects = [p for p in projects if not p.get("private", True)]

    name = get_display_name(cv_data)
    headline = (cv_data.get("headline") or "Senior Software Engineer").strip()
    summary = (cv_data.get("summary") or "").strip()
    tagline = summary.split(". ")[0].strip() + "." if summary else "Specializing in full-stack development, DevOps practices, and scalable solutions that drive business growth."
    if len(tagline) > 200:
        tagline = tagline[:197] + "..."
    experience_summary = "5+ years"
    experience_entries = cv_data.get("experience_entries") or []
    if experience_entries and isinstance(experience_entries[0], dict):
        experience_summary = "5+ years"

    ctx = {
        "name": name,
        "title": headline.split("|")[0].strip() if "|" in headline else headline,
        "headline": headline,
        "badge_label": "Available for Work",
        "experience_summary": experience_summary + " of expertise.",
        "highlight_years": experience_summary if experience_summary else "5+ years",
        "tagline": tagline,
        "resume_url": "cv.pdf",
        "github_url": "#",
        "linkedin_url": "#",
        "image_url": "img/me.jpeg",
        "email": (cv_data.get("email") or "").strip() or "your@email.com",
        "phone": (cv_data.get("mobile_number") or cv_data.get("phone") or "").strip() or "—",
        "location": "Cape Town, South Africa",
    }

    experience_cards = build_experience_html(cv_data)
    education_cards = build_education_html(cv_data)
    cert_cards = build_certifications_html(cv_data)
    project_cards = build_projects_html(projects)

    # Full page matching index.html structure and classes
    nav_html = f"""      <nav class="nav">
  <div class="nav-inner container">
    <div class="nav-brand">{_e(name)}</div>
    <button class="nav-toggle" id="navToggle" aria-label="Toggle navigation">
      <span></span>
      <span></span>
      <span></span>
    </button>
    <div class="nav-links" id="navLinks">
      <a href="#home">Home</a>
      <a href="#skills">Skills</a>
      <a href="#experience">Experience</a>
      <a href="#projects">Projects</a>
      <a href="#contact">Contact</a>
    </div>
  </div>
</nav>
"""

    experience_section = f"""  <section id="experience" class="section">
  <div class="container">
    <header class="section-header">
      <h2>Professional Experience</h2>
      <p>
        Over 5 years of experience building scalable web applications and leading development teams in fast-paced environments.
      </p>
    </header>

    <div class="stacked-cards">
{experience_cards if experience_cards else '      <p class="muted">No experience data.</p>'}
    </div>

    <header class="section-header" style="margin-top: 3rem;">
      <h2>Education</h2>
      <p>
        Formal education and professional certifications underpinning my experience in networking, information systems, and software development.
      </p>
    </header>

    <div class="stacked-cards">
{education_cards if education_cards else '      <p class="muted">No education data.</p>'}
    </div>

    <header class="section-header" style="margin-top: 3rem;">
      <h2>Certifications</h2>
    </header>

    <div class="stacked-cards">
{cert_cards if cert_cards else '      <p class="muted">None listed.</p>'}
    </div>
  </div>
</section>
"""

    projects_section = f"""  <section id="projects" class="section section-alt">
  <div class="container">
    <header class="section-header">
      <h2>Featured Projects</h2>
      <p>
        A selection of projects that demonstrate expertise in full-stack development and modern DevOps practices.
      </p>
    </header>

    <div class="grid projects-grid">
{project_cards if project_cards else '      <p class="muted">No projects data yet.</p>'}
    </div>
  </div>
</section>
"""

    contact_section = f"""  <section id="contact" class="section">
  <div class="container">
    <header class="section-header">
      <h2>Let's Work Together</h2>
      <p>
        Ready to bring your next project to life? Let's discuss how my expertise can help achieve your goals.
      </p>
    </header>

{build_contact_html(ctx)}
  </div>
</section>
"""

    footer_html = f"""      <footer class="footer">
  <div class="container">
    <h3>{_e(name)}</h3>
    <p class="muted">
      {_e(ctx["title"])} | Full-Stack Developer | DevOps Enthusiast
    </p>
  </div>
</footer>
"""

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Senior Software Engineer Portfolio</title>
    <link rel="stylesheet" href="css/styles.css" />
  </head>
  <body>
    <div class="page">
{nav_html}
      <main>
{build_hero_html(ctx)}
{build_skills_html(skill_categories, tech_stack)}
{experience_section}
{projects_section}
{contact_section}
      </main>

{footer_html}
    </div>

    <script>
      const navToggle = document.getElementById('navToggle');
      const navLinks = document.getElementById('navLinks');

      if (navToggle && navLinks) {{
        navToggle.addEventListener('click', () => {{
          navLinks.classList.toggle('nav-links-open');
        }});
      }}
    </script>
  </body>
</html>
"""

    SITE_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_doc)

    print(f"Wrote {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
