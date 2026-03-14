"""
Shared utilities and path constants for the generator scripts.
Used by generate_site, generate_readme, and generate_portfolio.
"""

import json
from pathlib import Path
from typing import Any, Optional

# Repo root (parent of scripts/)
_ROOT = Path(__file__).resolve().parent.parent

ROOT = _ROOT
DATA_DIR = _ROOT / "data"
TEMPLATES_DIR = _ROOT / "templates"
REPORTS_DIR = _ROOT / "reports"
PORTFOLIO_DIR = _ROOT / "portfolio"
SITE_DIR = _ROOT / "site"


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
