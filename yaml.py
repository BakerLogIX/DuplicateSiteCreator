"""Tiny YAML loader to support config parsing without external deps."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Union, IO


def safe_load(stream: Union[str, IO[str]]) -> Dict[str, Any]:
    raw = stream.read() if hasattr(stream, "read") else str(stream)
    lines = [line.rstrip() for line in raw.splitlines() if line.strip() and not line.strip().startswith("#")]
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
            new_dict: Dict[str, Any] = {}
            current[key] = new_dict
            stack.append(new_dict)
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
