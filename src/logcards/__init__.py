"""logcards — render JSONL/text logs as styled terminal cards.

Public API:

* :func:`load_rules` — load card rules from one or more YAML directories.
* :class:`RuleMatcher` — pick the highest-priority matching card.
* :class:`CardEngine` — evaluate a record into a :class:`RenderContext`.
* :class:`TerminalCardRenderer` — render a context as a Rich panel.
* :class:`JsonlStreamer` — stream records from files/stdin.
* :func:`parse_monolog` — normalize monolog JSON or Symfony-text lines.
"""

from __future__ import annotations

from .engine import CardEngine, RenderContext
from .matcher import RuleMatcher
from .monolog import human_datetime, parse_monolog
from .renderers import TerminalCardRenderer, format_payload
from .renderers.base import CardRenderer
from .rules import CardRender, CardRule, Matcher, Payload, load_rules
from .streamer import JsonlStreamer

__all__ = [
    "CardRule",
    "CardRender",
    "Matcher",
    "Payload",
    "load_rules",
    "RuleMatcher",
    "CardEngine",
    "RenderContext",
    "CardRenderer",
    "TerminalCardRenderer",
    "format_payload",
    "JsonlStreamer",
    "parse_monolog",
    "human_datetime",
]
