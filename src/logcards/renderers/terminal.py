"""Terminal renderer using Rich (2-col grid + full-width payload)."""

from __future__ import annotations

from typing import Any

from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from ..engine import RenderContext
from . import formatters
from .base import CardRenderer


class TerminalCardRenderer(CardRenderer):
    def __init__(self, theme: str = "monokai") -> None:
        self.theme = theme

    def render(self, ctx: RenderContext, raw_record: dict[str, Any]) -> Panel:
        # Matched rule card.
        if ctx.rule_id is not None:
            return self._render_card(ctx)
        # Unmatched JSON or rule-less record -> syntax-highlighted JSON.
        return self._render_fallback(raw_record, ctx)

    def _render_fallback(self, raw: dict[str, Any], ctx: RenderContext) -> Panel:
        pretty = formatters.format_payload(raw, "json")
        return Panel(
            Syntax(pretty, "json", theme=self.theme),
            title="📄 [dim]Unmatched JSON[/dim]",
            border_style="dim white",
            expand=False,
        )

    def _render_card(self, ctx: RenderContext) -> Panel:
        title = ctx.title
        if ctx.badge:
            title = f"{ctx.title} [reverse] {ctx.badge} [/]"

        grid = Table.grid(expand=False)

        if ctx.fields:
            meta = Table.grid(padding=(0, 2))
            meta.add_column(style="bold")
            meta.add_column(style="")
            for k, v in ctx.fields:
                meta.add_row(f"{k}:", v)
            grid.add_row(meta)

        if ctx.payload is not None:
            grid.add_row(
                Text.from_markup("[dim]─── payload ────────────────────────────[/]")
            )
            payload_text = formatters.format_payload(ctx.payload, ctx.payload_formatter)
            grid.add_row(Text(payload_text))

        if ctx.unmapped_fields:
            grid.add_row(
                Text.from_markup("[dim]─── ⋯ unmapped ────────────────────────[/]")
            )
            extra = Table.grid(padding=(0, 2))
            extra.add_column(style="dim yellow")
            extra.add_column(style="dim white")
            for k, v in ctx.unmapped_fields.items():
                extra.add_row(f"{k}:", formatters.format_payload(v, "raw"))
            grid.add_row(extra)

        return Panel(
            grid if grid.row_count else Text(""),
            title=title,
            subtitle=f"[dim]{ctx.timestamp}[/dim]" if ctx.timestamp else None,
            subtitle_align="right",
            border_style=ctx.border,
            expand=False,
        )
