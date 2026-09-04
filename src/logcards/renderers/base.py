"""Abstract renderer interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..engine import RenderContext


class CardRenderer(ABC):
    @abstractmethod
    def render(self, ctx: RenderContext, raw_record: dict[str, Any]) -> Any:
        """Render a card context to a target representation."""
        raise NotImplementedError
