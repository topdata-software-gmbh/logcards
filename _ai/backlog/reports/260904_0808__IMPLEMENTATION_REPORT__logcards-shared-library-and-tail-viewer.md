---
filename: "_ai/backlog/reports/260904_0808__IMPLEMENTATION_REPORT__logcards-shared-library-and-tail-viewer.md"
title: "Report: logcards shared library + standalone tail viewer"
createdAt: 2026-09-04 08:08
updatedAt: 2026-09-04 08:08
project: "logcards"
status: completed
filesCreated: 16
filesModified: 4
filesDeleted: 7
tags: [logcards, python, rich, cards, monolog, telemetry, open-source]
documentType: IMPLEMENTATION_REPORT
---

# Implementation Report: shared `logcards` library + standalone `logcards tail` viewer

## 1. Summary

Extracted the card-rendering engine that previously lived inside
`super-bin` (`sb.core.logcards`) into a new, standalone, **open-source
Python package `logcards`** that is shared by `sb tail` (private
super-bin) and will be consumed by `tt log` (topdata-tools). The package
ships the engine, monolog JSON + Symfony-text parsers, bundled sample card
definitions, and a **self-sufficient `logcards tail` CLI**. `super-bin`
was refactored to depend on the new package, and `sb tail` was validated
to render identically before/after.

## 1.5 Prompt used

> "i have a log of jobs .. you can check local clones /topdata/clones ..
> but the live shops write the files just in local volume folders .. any
> idea how i can use my cards logger to display these logs sw6 logs nicely
> .. maybe we can extend /topdata/topdata-node-agent-v2? or some ssh-tai?
> also check /topdata/topdata-tools where i have (or plan to) having site
> namespace for managing sites .. maybe we could add there a command for
> tailing prod logs (in json format)"

Followed by a brainstorm that settled: shared Python engine, open-source
GitHub repo, extracted engine + monolog parsers + sample defs, a local-only
`logcards tail` CLI, and remote/SSH tailing deferred to `tt log`.

## 2. Files Changed

### New repo `/topdata/logcards` (open source, MIT)

**Created (package):**
- `pyproject.toml` — hatch build, `logcards` console script, micro-deps
  (`typer`, `rich`, `PyYAML`), ruff/black/mypy config, wheel artifacts for
  the YAML card defs.
- `src/logcards/rules.py` — pure card-rule models (`CardRule`, `Matcher`,
  `CardRender`, `CardField`, `Payload`) + `load_rules()` (extracted from
  sb `config.py`, minus sb.settings coupling).
- `src/logcards/matcher.py` — `RuleMatcher` (priority-based).
- `src/logcards/engine.py` — `CardEngine` + `RenderContext` (unused-key
  tracking, payload prep).
- `src/logcards/streamer.py` — `JsonlStreamer` (files/stdin, backlog +
  follow).
- `src/logcards/monolog.py` — **new**: parses both monolog JSON
  (`formatter: monolog.formatter.json`) and Symfony text lines into a
  normalized `{message, level_name, channel, datetime, exception_class}`.
- `src/logcards/cli.py` — **new**: `logcards tail` Typer command + card-dir
  resolution (`--cards` / `[tail] card_dirs` config / default).
- `src/logcards/renderers/` — `base.py`, `formatters.py`, `terminal.py`
  (extracted from sb).
- `src/logcards/__init__.py` — public API re-exports.
- `src/logcards/py.typed` — strict-mypy marker.
- `src/logcards/card_definitions/` — `__init__.py` (exposes
  `CARD_DEFINITIONS_DIR`) + `monolog.yaml` (new), `mcp-tool-usage.yaml`,
  `skill-usage.yaml` (ported).
- `tests/` — `test_monolog.py`, `test_matcher.py`, `test_rules.py`,
  `test_renderer.py`.
- `README.md` — rewritten with full usage + schema docs.
- `_ai/backlog/reports/260904_0808__IMPLEMENTATION_REPORT__...md` — this
  report.

**Modified:** `CHANGELOG.md` (README exists; CHANGELOG pending a versioned
release).

### `super-bin` (refactored)

- `src/sb/core/logcards/config.py` — [modify] slimmed to only the sb
  `resolve_config()` (keeps `sb.core.settings` coupling); re-exports
  `CardRule`, `load_rules` from `logcards`.
- `src/sb/core/logcards/__init__.py` — [modify] now exports
  `CardRule`, `LogCardsConfig`, `load_rules`, `resolve_config`.
- `src/sb/commands/tail_cmd.py` — [modify] imports engine/matcher/
  renderer/streamer from `logcards` instead of local modules.
- `pyproject.toml` + `uv.lock` — [modify] added `logcards` git/path
  dependency.
- `tests/test_logcards.py` — [modify] imports moved to `logcards`.
- `src/sb/core/logcards/{engine,matcher,streamer}.py` and
  `renderers/` — [deleted] moved to `logcards` package.
- `_ai/backlog/active/260903_2126__IMPLEMENTATION_PLAN__logcards-shared-library-and-tail-viewer.md` — [created] plan.

## 3. Key Changes

- Extracted the entire card engine (matcher, engine, renderers, streamer,
  rule loading) from `super-bin` into a standalone `logcards` package with
  **zero coupling to any CLI's config system** (`rules.py` is pure).
- Added a **monolog parser** that normalizes both Shopware 6 log formats
  (JSON formatter + Symfony text) into stable keys, including
  `exception_class` extraction from FQCN (`NotFoundHttpException`,
  `Symfony\Component\...\Exception\...`) for both dict and string
  exception contexts.
- Added a **standalone `logcards tail` CLI** — local-only by design
  (files/stdin), auto-detects monolog vs generic JSON, renders cards.
- `sb tail` now delegates to `logcards`; its sb-settings-bound
  `resolve_config` is the only thing kept local.
- Bundled sample card defs travel **inside the wheel** (hatch `artifacts`
  includes the YAML files + `py.typed` for strict mypy).

## 4. Deviations from Plan

- **Build config friction (hatchling):** initial `force-include` for the
  card YAMLs caused a "second file added at the same path" wheel error
  (because `card_definitions` is a normal package). Switched to
  `[tool.hatch.build.targets.wheel.artifacts]` as an array of globs —
  which itself initially failed ("must be an array of strings") because
  I wrote it as a dict. Final form is `artifacts =
  ["src/logcards/card_definitions/*.yaml"]`.
- **mypy strict / `py.typed`:** the shared package initially triggered
  `[import-untyped]` under super-bin's strict mypy. Fixed by adding a
  `py.typed` marker to the logcards package and forcing a reinstall
  (`uv sync --reinstall-package logcards`) so the built copy carried it.
- **Symfony exception-class extraction:** the greedy trailing-JSON regex
  missed the common `message {...} []` shape (extra as `[]`, not `{}`),
  and the exception FQCN contains backslashes. Reworked the regex to
  non-greedy `{...?}` + `{...}|[...]`, and parse `exception_class` as the
  last `\`-separated segment.
- **Duplicate `/tmp` not an issue,** but `logger` coverage in
  `parse_monolog` confirms the two branches ({json} {json} vs {json} []).

## 5. Technical Decisions

- **Python + Rich** (not Go) — both consumers (`sb`, `tt`) are Python and
  already use Rich; sharing one engine beats introducing a second
  language/ecosystem.
- **Standalone `logcards tail` is local-only** — remote/SSH tailing lives
  in higher-level wrappers (`tt log`) to keep the open-source tool
  dependency-free and generic.
- **`card_definitions/` ships inside the package** (`CARD_DEFINITIONS_DIR`)
  so both CLIs and the standalone binary can point at bundled defs without
  path magic.
- **Dual-format monolog parsing in the library** — enables the plan to roll
  the JSON formatter out to the other ~27 SW6 shops while still rendering
  the existing Symfony-text shops today.
- **`resolve_config` stays in super-bin** — the sb `[tail]` scalar
  resolution depends on `sb.core.settings`; keeping it local avoids leaking
  sb's config system into the shared library.

## 6. Testing Notes

- `/topdata/logcards`: `uv run pytest tests/` → 20 passed. ruff clean,
  black `--check` clean, `uv run mypy src` → no issues.
- `/topdata/logcards`: `uv build` succeeds; the wheel includes the YAML
  card defs and `py.typed`.
- `/home/marc/devel/super-bin`: `uv run pytest tests/` → 555 passed;
  ruff/black clean; `uv run mypy src/sb/commands/tail_cmd.py
  src/sb/core/logcards/` → no issues (pre-existing llm-router mypy errors
  elsewhere are unrelated).
- **End-to-end `sb tail`** renders identically before/after the refactor
  (both `--card-dirs` and config-only paths).
- **Standalone `logcards tail`** validated against real data:
  - Symfony text: `/topdata/clones/citeq/vol/www/var/log/prod-2025-12-29.log`
    → `ERROR`/`request` card with `Not FoundHttpException`, full context
    payload.
  - JSON: `/topdata/clones/sw67/vol/www/var/log/dev-2026-09-03.log` →
    `CRITICAL`/`console` card, humanized datetime.
  - Telemetry: opencode `mcp-tool-usage.jsonl` / `skill-usage.jsonl` cyan/
    magenta cards.

## 7. Usage Examples

```bash
# Standalone — Shopware prod log (Symfony text)
logcards tail --cards src/logcards/card_definitions \
  /path/to/clones/<shop>/vol/www/var/log/prod-2026-09-03.log

# Standalone — opencode telemetry (JSONL)
logcards tail --cards src/logcards/card_definitions \
  ~/.local/share/opencode/telemetry/mcp-tool-usage.jsonl

# Pipe stdin
cat logs.jsonl | logcards tail --cards src/logcards/card_definitions

# Non-following, show last 20
logcards tail --no-follow -n 20 --cards ... file.log

# Config-driven card dirs (~/.config/logcards/config.toml)
#   [tail]
#   card_dirs = ["/topdata/logcards/src/logcards/card_definitions"]

# As a library
from logcards import load_rules, RuleMatcher, CardEngine, TerminalCardRenderer
rules = load_rules(card_dirs=[CARD_DEFINITIONS_DIR])
matcher = RuleMatcher(rules)
ctx = CardEngine().process(record, matcher.match(record))
print(TerminalCardRenderer().render(ctx, record))

# sb tail now uses the shared engine
sb tail --card-dirs /topdata/logcards/src/logcards/card_definitions \
  /home/marc/.local/share/opencode/telemetry/*.jsonl
```

## 8. Documentation Updates

- `/topdata/logcards/README.md` — full rewrite: features, install, CLI +
  library usage, card-definition schema, dev commands.
- Implementation plan recorded at
  `super-bin/_ai/backlog/active/260903_2126__IMPLEMENTATION_PLAN__logcards-shared-library-and-tail-viewer.md`.

## 9. Next Steps

- **`tt log`** (topdata-tools): `tt log ls`, `tt log tail <shop> [--remote]`
  (SSH `tail -f` via existing `tt.core.ssh` + `misc/mount-sites.conf`),
  `tt log format` (roll out `formatter: monolog.formatter.json` across the
  other ~27 shops), and a deferred `tt log watch` Textual TUI.
- **Commit + push** the `logcards` repo (currently uncommitted) and add a
  CHANGELOG entry / v0.1.0 tag.
- Consider publishing `logcards` to PyPI for pip installs on arbitrary
  machines (currently consumed via `uv` path/git dependency).
