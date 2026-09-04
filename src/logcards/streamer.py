"""Multi-file + stdin streaming with plain-text passthrough.

Yields ``(source_label, line)`` where *line* is either a parsed JSON dict
or a raw text string (so callers can render cards or pass text through).
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Generator, TextIO

Record = dict[str, object]


class JsonlStreamer:
    def __init__(
        self, paths: list[Path], lines_backlog: int = 10, use_stdin: bool = False
    ) -> None:
        self.paths = [p for p in paths if p.exists() and p.is_file()]
        self.lines_backlog = lines_backlog
        self.use_stdin = use_stdin

    @staticmethod
    def _parse(line: str) -> object:
        stripped = line.strip()
        if not stripped:
            return None  # skip blank lines
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            return stripped  # plain-text passthrough

    def read_backlog(self) -> Generator[tuple[str, object], None, None]:
        for path in self.paths:
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    for line in fh.readlines()[-self.lines_backlog :]:
                        parsed = self._parse(line)
                        if parsed is not None:
                            yield str(path), parsed
            except OSError:
                continue
        if self.use_stdin:
            for line in sys.stdin:
                parsed = self._parse(line)
                if parsed is not None:
                    yield "<stdin>", parsed

    def follow(
        self, poll_interval: float = 0.1
    ) -> Generator[tuple[str, object], None, None]:
        handles: dict[Path, TextIO] = {}
        for path in self.paths:
            try:
                fh: TextIO = open(path, "r", encoding="utf-8")  # noqa: SIM115
                fh.seek(0, 2)  # EOF
                handles[path] = fh
            except OSError:
                continue
        try:
            while True:
                had_activity = False
                for path, fh in list(handles.items()):
                    line = fh.readline()
                    if line:
                        had_activity = True
                        parsed = self._parse(line)
                        if parsed is not None:
                            yield str(path), parsed
                if self.use_stdin and not sys.stdin.isatty():
                    for line in sys.stdin:
                        had_activity = True
                        parsed = self._parse(line)
                        if parsed is not None:
                            yield "<stdin>", parsed
                if not had_activity:
                    time.sleep(poll_interval)
        finally:
            for fh in handles.values():
                fh.close()
