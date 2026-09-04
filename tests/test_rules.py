"""Tests for card rule loading and rendering."""

from pathlib import Path

import yaml

from logcards.rules import load_rules


def _write_card(
    path: Path, rule_id: str = "test", key_exist: list[str] | None = None, **kwargs
) -> None:  # noqa: E501
    data = {
        "id": rule_id,
        "priority": kwargs.get("priority", 0),
        "matcher": {"key_exist": key_exist or []},
        "render": {
            "title": kwargs.get("title", "Event"),
            "border": kwargs.get("border", "blue"),
            "fields": kwargs.get("fields", []),
        },
    }
    path.write_text(yaml.dump(data), encoding="utf-8")


def test_load_rules_single_dir(tmp_path):
    _write_card(tmp_path / "a.yaml", rule_id="a", key_exist=["x"])
    rules = load_rules(card_dirs=[tmp_path])
    assert len(rules) == 1
    assert rules[0].id == "a"


def test_load_rules_dedup_by_name(tmp_path):
    _write_card(tmp_path / "a.yaml", rule_id="a_first", key_exist=["x"])
    dir2 = tmp_path / "d2"
    dir2.mkdir()
    _write_card(dir2 / "a.yaml", rule_id="a_second", key_exist=["y"])
    rules = load_rules(card_dirs=[tmp_path, dir2])
    # First occurrence wins
    assert len(rules) == 1
    assert rules[0].id == "a_first"


def test_load_rules_project_layer_overrides(tmp_path):
    # Global layer
    _write_card(tmp_path / "a.yaml", rule_id="global")
    # Project layer
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / ".logcards").mkdir()
    _write_card(proj / ".logcards" / "a.yaml", rule_id="project")
    rules = load_rules(card_dirs=[tmp_path], project_dir=proj)
    assert rules[0].id == "project"
