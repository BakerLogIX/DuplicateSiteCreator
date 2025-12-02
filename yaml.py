"""Tiny YAML loader used when PyYAML is unavailable."""
from __future__ import annotations

import re
from typing import Any, Dict, IO, List, Union


def safe_load(stream: Union[str, IO[str]]) -> Dict[str, Any]:
    """Parse a minimal subset of YAML into a Python dict.

    The parser supports nested dictionaries defined by two-space indentation,
    integer and float scalars, and string values. Comment-only and blank lines
    are ignored to keep project configuration readable without external
    dependencies.
    """

    raw = stream.read() if hasattr(stream, "read") else str(stream)
    lines = [
        line.rstrip()
        for line in raw.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    root: Dict[str, Any] = {}
    stack: List[Dict[str, Any]] = [root]
    indents = [0]

    for line in lines:
        indent = len(line) - len(line.lstrip(" "))
        key, _, value = line.lstrip().partition(":")
        key = key.strip()
        value = value.strip().strip('"')

        while indent < indents[-1]:
            stack.pop()
            indents.pop()

        current = stack[-1]
        if value:
            current[key] = _parse_value(value)
        else:
            nested: Dict[str, Any] = {}
            current[key] = nested
            stack.append(nested)
            indents.append(indent + 2)

    return root


def _parse_value(value: str) -> Any:
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    try:
        return float(value)
    except ValueError:
        return value


__all__ = ["safe_load"]
