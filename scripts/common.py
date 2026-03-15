"""
Shared utilities and path constants for the generator scripts.
Used by generate_site, generate_readme, and generate_portfolio.
"""

import json
import os
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv

# Ensure environment variables from .env are available (e.g. GITHUB_TOKEN)
load_dotenv()

# Repo root (parent of scripts/)
_ROOT = Path(__file__).resolve().parent.parent

ROOT = _ROOT
DATA_DIR = _ROOT / "data"
TEMPLATES_DIR = _ROOT / "templates"
REPORTS_DIR = _ROOT / "reports"
PORTFOLIO_DIR = _ROOT / "portfolio"
SITE_DIR = _ROOT / "site"


def get_github_user_name(token: Optional[str] = None) -> Optional[str]:
    """Fetch the authenticated user's display name from GitHub API (GET /user).
    Returns profile 'name' if set, else 'login'. Returns None on missing token or API error.
    """
    token = token or os.environ.get("GITHUB_TOKEN")
    if not token or not str(token).strip():
        return None
    try:
        import requests
        r = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"},
            timeout=10,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        name = (data.get("name") or "").strip()
        if name:
            return name
        return (data.get("login") or "").strip() or None
    except Exception:
        return None


def get_display_name(cv_data: Optional[dict] = None, fallback: str = "Yoweli Kachala") -> str:
    """Resolve display name: GitHub profile name > CV first_name + last_name > CV name > fallback."""
    name = get_github_user_name()
    if name:
        return name
    if cv_data:
        first = (cv_data.get("first_name") or "").strip()
        last = (cv_data.get("last_name") or "").strip()
        if first or last:
            return f"{first} {last}".strip()
        name = (cv_data.get("name") or "").strip()
        if name:
            return name
    return fallback


def load_json(path: Path, default: Optional[Any] = None) -> Any:
    """
    Load JSON from path. On missing file or decode error, return default.
    If default is None, returns None (for callers that want to distinguish missing vs empty).
    """
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def render_template(template: str, context: dict) -> str:
    """Replace {{ key }} placeholders with context values (values are coerced to str)."""
    result = template
    for key, value in context.items():
        placeholder = "{{ " + key + " }}"
        result = result.replace(placeholder, str(value))
    return result
