"""Card data evaluation: unused-key tracking and payload preparation."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from .rules import CardRule


@dataclass
class RenderContext:
    title: str
    border: str
    badge: str | None
    timestamp: str | None
    fields: list[tuple[str, str]] = field(default_factory=list)
    payload: Any = None  # prepared payload value
    payload_formatter: str = "raw"
    unmapped_fields: dict[str, Any] = field(default_factory=dict)
    rule_id: str | None = None


class CardEngine:
    """Extracts card data and identifies leftover unmapped fields."""

    PLACEHOLDER = re.compile(r"\{([a-zA-Z0-9_]+)\}")

    @staticmethod
    def extract_keys(template: str | None) -> set[str]:
        if not template:
            return set()
        return set(CardEngine.PLACEHOLDER.findall(template))

    @staticmethod
    def format_value(val: Any) -> str:
        if isinstance(val, (dict, list)):
            return json.dumps(val, ensure_ascii=False)
        return str(val)

    def process(
        self,
        record: dict[str, Any],
        rule: CardRule | None,
        show_unmapped: bool = True,
    ) -> RenderContext:
        if rule is None:
            return RenderContext(
                title="Unmatched JSON",
                border="dim white",
                badge=None,
                timestamp=None,
                unmapped_fields=record if show_unmapped else {},
                rule_id=None,
            )

        render = rule.render
        used: set[str] = set()
        used.update(self.extract_keys(render.title))
        used.update(self.extract_keys(render.badge))
        used.update(self.extract_keys(render.timestamp))
        for f in render.fields:
            used.update(self.extract_keys(f.value))
        if render.timestamp:
            used.add("timestamp")
        if render.payload:
            used.add(render.payload.source)

        safe = {k: self.format_value(v) for k, v in record.items()}

        def fmt(tmpl: str | None) -> str | None:
            if not tmpl:
                return None
            try:
                return tmpl.format_map(safe)
            except KeyError:
                return tmpl

        unmapped: dict[str, Any] = {}
        # Per-card override, then global default.
        effective_show = (
            render.show_unmapped if render.show_unmapped is not None else show_unmapped
        )
        if effective_show:
            unmapped = {k: v for k, v in record.items() if k not in used}

        payload_val = None
        if render.payload:
            payload_val = record.get(render.payload.source)

        return RenderContext(
            title=fmt(render.title) or rule.id,
            border=render.border,
            badge=fmt(render.badge),
            timestamp=fmt(render.timestamp),
            fields=[(fmt(f.key) or f.key, fmt(f.value) or "") for f in render.fields],
            payload=payload_val,
            payload_formatter=render.payload.formatter if render.payload else "raw",
            unmapped_fields=unmapped,
            rule_id=rule.id,
        )
