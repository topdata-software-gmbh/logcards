"""Standalone ``logcards tail`` CLI.

Reads local files (or stdin), streams lines, parses them (auto-detecting
monolog JSON / Symfony text / generic JSON), matches cards, and prints
Rich cards to stdout.

Local only by design — remote/SSH tailing lives in higher-level wrappers
(e.g. ``tt log``).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from .engine import CardEngine
from .matcher import RuleMatcher
from .monolog import human_datetime, parse_monolog
from .renderers.terminal import TerminalCardRenderer
from .rules import load_rules
from .streamer import JsonlStreamer

DEFAULT_CONFIG_DIR = "~/.config/logcards/"

app = typer.Typer(help="Render JSONL/text logs as styled terminal cards.")
console = Console()


def _resolve_card_dirs(
    card_dirs: Optional[list[Path]], config_dir: Optional[Path]
) -> list[Path]:
    """Merge CLI + config card dirs; fall back to the default dir.

    CLI ``--card-dirs`` beats the ``[tail] card_dirs`` list in the config
    file, which beats the code default. Missing dirs are dropped.
    """
    import configparser

    raw: list[Path] = []

    # Config file: ~/.config/logcards/config.toml, [tail] card_dirs
    config_candidates = []
    if config_dir is not None:
        config_candidates.append(config_dir / "config.toml")
    config_candidates.append(Path(DEFAULT_CONFIG_DIR).expanduser() / "config.toml")
    for cfg in config_candidates:
        if cfg.is_file():
            parser = configparser.ConfigParser()
            try:
                parser.read(cfg)
                if parser.has_option("tail", "card_dirs"):
                    vals = parser.get("tail", "card_dirs")
                    parsed = (x.strip().strip('"').strip("'") for x in vals.split(","))
                    raw.extend(Path(x) for x in parsed if x)
            except configparser.Error:
                pass
            break

    raw.extend(card_dirs or [])

    seen: set[Path] = set()
    out: list[Path] = []
    for p in raw:
        abs_p = p.expanduser()
        if abs_p in seen:
            continue
        seen.add(abs_p)
        if abs_p.is_dir():
            out.append(abs_p)
    if not out:
        default = (Path(DEFAULT_CONFIG_DIR).expanduser() / "logcards").expanduser()
        out = [default] if default.is_dir() else []
    return out


@app.command()
def tail(
    files: list[Path] = typer.Argument(
        None,
        help="Log files to tail (defaults to stdin if none). Supports globs.",
    ),
    follow: bool = typer.Option(
        True,
        "-f",
        "--follow/--no-follow",
        help="Follow files continuously (like tail -f)",
    ),
    lines: int = typer.Option(
        10, "-n", "--lines", help="Backlog lines per file (0 = none)"
    ),
    cards: Optional[list[Path]] = typer.Option(
        None,
        "--cards",
        "--card-dirs",
        help="Card directories to load (overrides config.toml [tail] card_dirs)",
    ),
    theme: str = typer.Option(
        "monokai", "--theme", help="Syntax theme for JSON/unmapped payloads"
    ),
    hide_unmapped: bool = typer.Option(
        False,
        "--hide-unmapped/--show-unmapped",
        help="Hide/show the unmapped-field tray",
    ),
) -> None:
    """Tail log files and render records as cards (or pass text through)."""
    card_dirs = _resolve_card_dirs(cards, None)
    rules = load_rules(card_dirs=card_dirs)
    matcher = RuleMatcher(rules)
    engine = CardEngine()
    renderer = TerminalCardRenderer(theme=theme)
    show_unmapped = not hide_unmapped

    use_stdin = not files
    streamer = JsonlStreamer(
        list(files or []), lines_backlog=lines, use_stdin=use_stdin
    )

    def emit(source: str, record: object) -> None:
        if isinstance(record, dict):
            monolog = parse_monolog(record)
            # Normalize monolog records so cards can match on channel/level.
            if monolog is not None:
                finalized: dict[str, object] = {
                    **record,
                    **monolog,
                    "datetime": (
                        human_datetime(str(monolog["datetime"]))
                        if monolog["datetime"]
                        else None
                    ),
                }
                record = finalized
            rule = matcher.match(record)
            ctx = engine.process(record, rule, show_unmapped=show_unmapped)
            console.print(renderer.render(ctx, record))
        else:
            text = str(record)
            monolog = parse_monolog(text)
            if monolog is not None:
                rule = matcher.match(monolog)
                ctx = engine.process(monolog, rule, show_unmapped=show_unmapped)
                console.print(renderer.render(ctx, monolog))
            else:
                console.print(text)

    for source, record in streamer.read_backlog():
        emit(source, record)

    if not follow:
        return

    try:
        for source, record in streamer.follow():
            emit(source, record)
    except KeyboardInterrupt:
        console.print("\n[dim]Stream stopped.[/dim]")
        raise typer.Exit(0)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
