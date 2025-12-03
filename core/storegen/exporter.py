"""Utilities to export generated storefronts for deployment."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Dict


def export_static_store(source_dir: Path | str, destination_dir: Path | str, overwrite: bool = False) -> Path:
    """Copy generated static files to a destination directory.

    Args:
        source_dir: Directory containing generated storefront assets.
        destination_dir: Target directory for the exported files.
        overwrite: Whether to allow overwriting an existing destination.

    Returns:
        Path to the destination directory.
    """

    source_path = Path(source_dir)
    destination_path = Path(destination_dir)

    if destination_path.exists() and not overwrite:
        raise FileExistsError(f"Destination {destination_path} already exists")

    shutil.copytree(source_path, destination_path, dirs_exist_ok=overwrite)
    return destination_path


def build_deployment_manifest(output_dir: Path | str) -> Dict[str, int]:
    """Prepare a simple manifest describing generated assets.

    The manifest can be extended in later phases to include hashes or
    metadata required by external platforms.
    """

    output_path = Path(output_dir)
    manifest: Dict[str, int] = {}
    for file in output_path.glob("*.html"):
        manifest[file.name] = file.stat().st_size
    return manifest
