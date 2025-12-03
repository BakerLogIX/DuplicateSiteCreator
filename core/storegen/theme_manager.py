"""Theme selection utilities for the store generator."""
from __future__ import annotations

from pathlib import Path


def get_theme_path(theme_id: str = "default") -> Path:
    """Return the filesystem path for the given theme.

    Args:
        theme_id: Identifier of the theme. Defaults to ``"default"``.

    Returns:
        Path to the theme directory containing Jinja2 templates.

    Raises:
        FileNotFoundError: If the theme directory does not exist.
    """

    theme_path = Path(__file__).resolve().parent / "templates" / theme_id
    if not theme_path.exists():
        raise FileNotFoundError(f"Theme '{theme_id}' not found at {theme_path}")
    return theme_path
