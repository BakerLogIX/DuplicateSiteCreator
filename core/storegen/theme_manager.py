"""Theme selection utilities."""
from pathlib import Path

DEFAULT_THEME = "default"


def get_theme_path(theme_id: str = DEFAULT_THEME) -> Path:
    themes_dir = Path(__file__).resolve().parent / "themes"
    themes_dir.mkdir(exist_ok=True)
    return themes_dir / theme_id
