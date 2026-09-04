"""Card rule models and card-directory loading.

Card definitions live as one YAML file per card type, in one or more
directories. This module holds the pure data models (:class:`Matcher`,
:class:`CardRule`, :class:`CardRender`, ...) and the loading helpers that
turn a directory of YAML files into a sorted list of rules.

This module intentionally has **no** dependency on any specific CLI's
config/settings system, so it can be shared between ``sb tail`` and
``tt log`` (and the standalone ``logcards`` CLI).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Matcher:
    """Match rules evaluated against a structured log record (dict)."""

    equal: dict[str, Any] = field(default_factory=dict)
    key_exist: list[str] = field(default_factory=list)
    not_empty: list[str] = field(default_factory=list)

    def matches(self, record: dict[str, Any]) -> bool:
        if self.equal and not all(record.get(k) == v for k, v in self.equal.items()):
            return False
        if self.key_exist and not all(k in record for k in self.key_exist):
            return False
        if self.not_empty and not all(bool(record.get(k)) for k in self.not_empty):
            return False
        return True


@dataclass
class CardField:
    key: str
    value: str


@dataclass
class Payload:
    source: str
    formatter: str = "raw"


@dataclass
class CardRender:
    title: str = "Event"
    border: str = "blue"
    badge: str | None = None
    timestamp: str | None = "{timestamp}"
    fields: list[CardField] = field(default_factory=list)
    payload: Payload | None = None
    show_unmapped: bool | None = None  # None -> fall back to global default


@dataclass
class CardRule:
    id: str
    priority: int = 0
    matcher: Matcher = field(default_factory=Matcher)
    render: CardRender = field(default_factory=CardRender)


def _parse_card_file(path: Path) -> CardRule:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    match = data.get("matcher", {}) or {}
    render = data.get("render", {}) or {}
    payload = render.get("payload")
    return CardRule(
        id=str(data.get("id", path.stem)),
        priority=int(data.get("priority", 0)),
        matcher=Matcher(
            equal=match.get("equal", {}) or {},
            key_exist=match.get("key_exist", []) or [],
            not_empty=match.get("not_empty", []) or [],
        ),
        render=CardRender(
            title=render.get("title", "Event"),
            border=render.get("border", "blue"),
            badge=render.get("badge"),
            timestamp=render.get("timestamp", "{timestamp}"),
            fields=[CardField(f["key"], f["value"]) for f in render.get("fields", [])],
            payload=Payload(**payload) if payload else None,
            show_unmapped=render.get("show_unmapped"),
        ),
    )


def load_rules(
    card_dirs: list[Path] | None = None, project_dir: Path | None = None
) -> list[CardRule]:
    """Load and merge all card rules, project layer overriding global.

    ``card_dirs`` is the already-resolved list of directories (the
    highest-priority first). A project-local ``.logcards/`` layer is
    prepended when ``project_dir`` is given and that directory exists.

    Rules with the same filename (basename) are deduped via ``setdefault``
    so the first occurrence wins (project layer beats global). Rules are
    then sorted by ``(priority DESC, filename ASC)`` so the matcher picks
    the highest-priority winner (tie -> file order, deterministic).
    """
    dirs: list[Path] = []
    if project_dir is not None:
        local = project_dir / ".logcards"
        if local.is_dir():
            dirs.append(local)
    if card_dirs:
        dirs.extend(card_dirs)

    by_name: dict[str, Path] = {}
    for d in dirs:  # project first wins over global
        for p in sorted(d.glob("*.yaml")):
            by_name.setdefault(p.stem, p)
    rules = [_parse_card_file(p) for p in by_name.values()]
    rules.sort(key=lambda r: (-r.priority, r.id))
    return rules
