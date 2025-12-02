"""Static store builder."""
from pathlib import Path
from typing import Iterable

from jinja2 import Environment, FileSystemLoader, select_autoescape

from core.logging.logger import get_logger
from core.storegen.theme_manager import DEFAULT_THEME, get_theme_path

logger = get_logger(__name__)


def _get_environment(theme_path: Path) -> Environment:
    loader = FileSystemLoader(str(theme_path))
    return Environment(loader=loader, autoescape=select_autoescape(["html", "xml"]))


def build_store(store_id: int, output_dir: str, theme_id: str = DEFAULT_THEME) -> None:
    theme_path = get_theme_path(theme_id)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    env = _get_environment(theme_path)
    index_template = env.from_string("<html><body><h1>Store {{ store_id }}</h1></body></html>")
    rendered = index_template.render(store_id=store_id)
    (output_path / "index.html").write_text(rendered, encoding="utf-8")
    logger.info("Store %s built at %s", store_id, output_path)
