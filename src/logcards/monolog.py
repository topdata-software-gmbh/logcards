"""Monolog / Shopware 6 log parsers.

Shopware 6 writes daily logs to ``var/log/<env>-YYYY-MM-DD.log`` in one of
two formats:

* **JSON** — when the ``rotating_file`` handler has
  ``formatter: monolog.formatter.json`` (one JSON object per line):
  ``{"message":..., "context":{...}, "level":500, "level_name":"CRITICAL",
  "channel":"request", "datetime":"...", "extra":{}}``

* **Symfony text** — the default ``LineFormatter``
  ``[ISO_TIMESTAMP] channel.LEVEL: message {json_context} {json_extra}``

:func:`parse_monolog` accepts either a raw text line or a structured
dict and returns a normalized dict with stable keys that card definitions
can match on (``message``, ``level_name``, ``channel``, ``datetime``).
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

_LEVELS = {
    "DEBUG": 100,
    "INFO": 200,
    "NOTICE": 250,
    "WARNING": 300,
    "ERROR": 400,
    "CRITICAL": 500,
    "ALERT": 550,
    "EMERGENCY": 600,
}

# [2026-09-03T07:15:09.611886+00:00] request.ERROR: message {"ctx"} {"extra"}
_TEXT_LINE = re.compile(
    r"^\[(?P<ts>[^\]]+)\]\s+(?P<channel>\S+)\.(?P<level>\w+):\s*(?P<message>.*)$"
)

# Trailing {json} [json] blobs inside the message portion.
# Symfony format: message {"context"} [] or message {"context"} {"extra"}
_TRAILING_JSON = re.compile(r"(\s*\{.*?\})\s*(\{.*\}|\[.*\])\s*$")


def _level_number(level_name: str) -> int:
    return _LEVELS.get(level_name.upper(), 0)


def _parse_json_record(record: dict[str, Any]) -> dict[str, Any]:
    """Normalize an already-parsed monolog JSON record."""
    level_name = str(record.get("level_name", "")).upper()
    context = record.get("context") or {}
    # Pull the exception class name out of context.exception for display.
    exception_class = None
    ex = context.get("exception")
    if isinstance(ex, dict):
        exception_class = ex.get("class")
    elif isinstance(ex, str):
        # Symfony text: "[object] (NS\Package\Exception(code: 0): ...)"
        m2 = re.search(r"^\[object\]\s+\(([^()]+)\(code:", ex)
        if m2:
            fqcn = m2.group(1).strip()
            exception_class = fqcn.split("\\")[-1]

    return {
        "message": record.get("message", ""),
        "level": record.get("level", _level_number(level_name)),
        "level_name": level_name or "INFO",
        "channel": record.get("channel", ""),
        "datetime": record.get("datetime"),
        "context": context,
        "extra": record.get("extra", {}) or {},
        "exception_class": exception_class,
    }


def _parse_text_line(line: str) -> dict[str, Any] | None:
    """Parse a Symfony text log line into a normalized record, or None."""
    m = _TEXT_LINE.match(line)
    if not m:
        return None
    level_name = m.group("level").upper()
    message = m.group("message").strip()

    context: dict[str, Any] = {}
    extra: dict[str, Any] = {}
    # Peel off trailing {json} context/extra blobs.
    jm = _TRAILING_JSON.search(message)
    if jm:
        try:
            context = json.loads(jm.group(1).strip())
        except (ValueError, TypeError):
            context = {}
        try:
            extra = json.loads(jm.group(2).strip())
        except (ValueError, TypeError):
            extra = {}
        message = message[: jm.start()].rstrip()

    exception_class = None
    ex = context.get("exception")
    if isinstance(ex, str):
        m2 = re.match(r"^\[object\] \(([^()]+)\(code:", ex)
        if m2:
            fqcn = m2.group(1).strip()
            exception_class = fqcn.split("\\")[-1]

    return {
        "message": message,
        "level": _level_number(level_name),
        "level_name": level_name,
        "channel": m.group("channel"),
        "datetime": m.group("ts"),
        "context": context,
        "extra": extra,
        "exception_class": exception_class,
    }


def parse_monolog(line: str | dict[str, Any]) -> dict[str, Any] | None:
    """Parse a monolog line (dict or text) into a normalized record.

    Returns ``None`` if the line isn't recognizable as monolog/Symfony
    log output (so the caller can fall back to plain JSON handling).
    """
    if isinstance(line, dict):
        # A monolog JSON record has level_num/channel; distinguish from
        # arbitrary JSON by the presence of level_name + message.
        if "level_name" in line or "channel" in line:
            return _parse_json_record(line)
        return None

    stripped = line.strip()
    if not stripped:
        return None
    if stripped.startswith("{"):
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError:
            return None
        if isinstance(data, dict) and ("level_name" in data or "channel" in data):
            return _parse_json_record(data)
        return None
    return _parse_text_line(line)


def human_datetime(dt_str: str | None) -> str | None:
    """Best-effort conversion of an ISO datetime string to a friendly form."""
    if not dt_str:
        return None
    text = dt_str
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
        return parsed.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return dt_str
