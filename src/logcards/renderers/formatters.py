"""Pluggable payload formatters (sql, json, raw)."""

from __future__ import annotations

import json
from typing import Any, Callable

Formatter = Callable[[Any], str]

REGISTRY: dict[str, Formatter] = {}


def register(name: str) -> Callable[[Formatter], Formatter]:
    def deco(fn: Formatter) -> Formatter:
        REGISTRY[name] = fn
        return fn

    return deco


@register("raw")
def format_raw(val: Any) -> str:
    return str(val)


@register("json")
def format_json(val: Any) -> str:
    if isinstance(val, str):
        try:
            return json.dumps(json.loads(val), indent=2, ensure_ascii=False)
        except (ValueError, TypeError):
            return val
    return json.dumps(val, indent=2, ensure_ascii=False)


@register("sql")
def format_sql(val: Any) -> str:
    text = str(val).strip()
    # Simple pass-through for v1; SQL *pretty* reformatting can layer in
    # later. Keeps multi-line statements readable as-is.
    return text


def format_payload(val: Any, name: str) -> str:
    fn = REGISTRY.get(name, format_raw)
    return fn(val)
