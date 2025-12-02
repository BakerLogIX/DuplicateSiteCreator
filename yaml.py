"""Lightweight YAML loader stub for environments without PyYAML.

This parser only supports a small subset of YAML used by the project's
configuration file (nested dictionaries with scalar string values).
"""
from __future__ import annotations

from typing import Dict


def _strip_quotes(value: str) -> str:
    if value.startswith("\"") and value.endswith("\""):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    return value


def safe_load(stream: str | object) -> Dict[str, object]:
    config: Dict[str, object] = {}
    current_section: str | None = None

    content = stream.read() if hasattr(stream, "read") else str(stream)

    for line in content.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        key, _, raw_value = line.strip().partition(":")
        value = raw_value.strip()
        if indent == 0:
            current_section = key
            if value:
                config[current_section] = _strip_quotes(value)
            else:
                config[current_section] = {}
        elif indent >= 2 and current_section:
            section = config.setdefault(current_section, {})
            section[key] = _strip_quotes(value)
    return config
