"""Priority-based rule matching for structured records."""

from __future__ import annotations

from typing import Any

from .rules import CardRule


class RuleMatcher:
    """Picks the highest-priority card whose matcher passes.

    Rules are pre-sorted by (priority DESC, id ASC) by ``load_rules``,
    so the first match returned is the winner (tie -> file order).
    """

    def __init__(self, rules: list[CardRule]) -> None:
        self.rules = rules

    def match(self, record: dict[str, Any]) -> CardRule | None:
        for rule in self.rules:
            if rule.matcher.matches(record):
                return rule
        return None
