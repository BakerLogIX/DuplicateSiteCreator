"""Lightweight Jinja2-compatible stubs for offline environments."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict

__all__ = ["Environment", "FileSystemLoader", "select_autoescape"]


class Template:
    def __init__(self, source: str):
        self.source = source

    def render(self, **context: Any) -> str:
        return _render_template(self.source, context)


def select_autoescape(_: Any = None) -> None:
    """Placeholder for API compatibility."""

    return None


class FileSystemLoader:
    def __init__(self, searchpath: str | Path):
        self.searchpath = Path(searchpath)

    def load(self, template_name: str) -> str:
        template_path = self.searchpath / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Template {template_name} not found in {self.searchpath}")
        return template_path.read_text(encoding="utf-8")


class Environment:
    def __init__(self, loader: FileSystemLoader, **_: Any) -> None:
        self.loader = loader

    def get_template(self, template_name: str) -> Template:
        return Template(self.loader.load(template_name))


VAR_PATTERN = re.compile(r"{{\s*(?P<expr>[^}]+)\s*}}")
FOR_PATTERN = re.compile(
    r"{%\s*for\s+(?P<var>\w+)\s+in\s+(?P<iter>\w+)\s*%}(?P<body>.*?){%\s*endfor\s*%}",
    re.DOTALL,
)
IF_PATTERN = re.compile(
    r"{%\s*if\s+(?P<expr>[^%]+)%}(?P<body>.*?){%\s*endif\s*%}",
    re.DOTALL,
)


def _resolve_expr(expr: str, context: Dict[str, Any]) -> Any:
    expr = expr.strip()
    parts = expr.split(".")
    value: Any = context
    for part in parts:
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            value = getattr(value, part, None)
    return value


def _render_loops(template: str, context: Dict[str, Any]) -> str:
    rendered = template
    match = FOR_PATTERN.search(rendered)
    while match:
        var_name = match.group("var")
        iterable = _resolve_expr(match.group("iter"), context) or []
        body = match.group("body")

        body_rendered = "".join(
            _render_template(body, {**context, var_name: item}) for item in iterable
        )
        rendered = rendered[: match.start()] + body_rendered + rendered[match.end() :]
        match = FOR_PATTERN.search(rendered)
    return rendered


def _render_conditionals(template: str, context: Dict[str, Any]) -> str:
    rendered = template
    match = IF_PATTERN.search(rendered)
    while match:
        expr_value = _resolve_expr(match.group("expr"), context)
        body = match.group("body") if expr_value else ""
        body_rendered = _render_template(body, context)
        rendered = rendered[: match.start()] + body_rendered + rendered[match.end() :]
        match = IF_PATTERN.search(rendered)
    return rendered


def _render_variables(template: str, context: Dict[str, Any]) -> str:
    def replace(match: re.Match[str]) -> str:
        value = _resolve_expr(match.group("expr"), context)
        return "" if value is None else str(value)

    return VAR_PATTERN.sub(replace, template)


def _render_template(template: str, context: Dict[str, Any]) -> str:
    rendered = _render_loops(template, context)
    rendered = _render_conditionals(rendered, context)
    rendered = _render_variables(rendered, context)
    return rendered
