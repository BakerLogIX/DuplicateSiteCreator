"""Placeholder exporter utilities."""
from pathlib import Path
from shutil import copytree

from core.logging.logger import get_logger

logger = get_logger(__name__)


def export_to_folder(source_dir: str, destination: str) -> Path:
    source_path = Path(source_dir)
    destination_path = Path(destination)
    if destination_path.exists():
        logger.warning("Destination %s already exists; contents may be overwritten.", destination)
    copytree(source_path, destination_path, dirs_exist_ok=True)
    logger.info("Exported store files from %s to %s", source_dir, destination)
    return destination_path
