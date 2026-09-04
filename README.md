# logcards

Render JSONL / text logs as styled terminal cards from YAML card definitions.

`logcards` is a small, dependency-light Python library plus a standalone
`logcards tail` CLI. It powers the card viewers in `sb tail` (super-bin)
and `tt log` (topdata-tools), sharing one card engine and one set of card
definitions across both.

## Features

- **Card definitions in YAML** — match on record keys (`key_exist`,
  `not_empty`, `equal`), then render a Rich panel with title, badge,
  timestamp, ordered fields, and a JSON/raw/sql payload.
- **Monolog / Shopware 6 parsing** — normalizes both the JSON
  (`formatter: monolog.formatter.json`) and the default Symfony text
  format into stable keys (`message`, `level_name`, `channel`,
  `datetime`, `exception_class`).
- **Standalone viewer** — `logcards tail [--cards DIR] [files...]`
  streams local files or stdin and prints cards. Local only by design;
  remote/SSH tailing lives in higher-level wrappers.
- **Bundled sample card defs** — Shipware `monolog.yaml` plus the opencode
  telemetry cards (`mcp-tool-usage.yaml`, `skill-usage.yaml`).

## Install

```bash
uv sync --extra dev          # development
# or as a dependency:
#   logcards = { git = "https://github.com/topdata-software-gmbh/logcards.git" }
```

## Usage

**Standalone CLI:**

```bash
# Shopware prod log (Symfony text format)
logcards tail --cards src/logcards/card_definitions \
  /path/to/vol/www/var/log/prod-2026-09-03.log

# opencode MCP tool telemetry (JSONL)
logcards tail --cards src/logcards/card_definitions \
  ~/.local/share/opencode/telemetry/mcp-tool-usage.jsonl

# pipe stdin
cat logs.jsonl | logcards tail --cards src/logcards/card_definitions

# non-following (print last N lines then exit)
logcards tail --no-follow -n 20 --cards ... file.log
```

Card dirs also resolve from `~/.config/logcards/config.toml`:

```toml
[tail]
card_dirs = ["/topdata/logcards/src/logcards/card_definitions"]
```

**Library:**

```python
from logcards import load_rules, RuleMatcher, CardEngine, TerminalCardRenderer

rules = load_rules(card_dirs=[CARD_DEFINITIONS_DIR])
matcher = RuleMatcher(rules)
engine = CardEngine()
renderer = TerminalCardRenderer(theme="monokai")

for record in records:                       # list[dict] from JSONL
    rule = matcher.match(record)
    ctx = engine.process(record, rule)
    print(renderer.render(ctx, record))
```

## Card definition schema

```yaml
id: my-card
priority: 10
matcher:
  key_exist: [field_a]
  not_empty: [field_a]
  equal: {type: "event"}         # optional
render:
  title: "{field_a}"
  border: "cyan"
  badge: "{server}"
  timestamp: "{timestamp}"
  fields:
    - key: status
      value: "{status}"
  payload:
    source: args                 # record key to show in full
    formatter: json              # raw | json | sql
  show_unmapped: true            # leftover record keys in a tray
```

## Development

```bash
uv run pytest tests/
uv run ruff check src tests
uv run black --check src tests
uv run mypy src
```

## License

MIT
