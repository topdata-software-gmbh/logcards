"""Access to the bundled sample card definitions.

Importable so both the standalone CLI and higher-level wrappers
(``sb tail``, ``tt log``) can point at the shipped defs:

    from logcards.card_definitions import CARD_DEFINITIONS_DIR

    rules = load_rules(card_dirs=[CARD_DEFINITIONS_DIR])
"""

from __future__ import annotations

from pathlib import Path

CARD_DEFINITIONS_DIR = Path(__file__).parent

__all__ = ["CARD_DEFINITIONS_DIR"]
