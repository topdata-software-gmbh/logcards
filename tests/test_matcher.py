"""Tests for matcher and engine."""

from logcards.engine import CardEngine
from logcards.matcher import RuleMatcher
from logcards.rules import CardRender, CardRule, Matcher


def _simple_rule(
    rule_id: str = "test",
    key_exist: list[str] | None = None,
    **kwargs: object,
) -> CardRule:
    return CardRule(
        id=rule_id,
        matcher=Matcher(key_exist=key_exist or [], **kwargs),
        render=CardRender(
            **{k: v for k, v in kwargs.items() if k in CardRender.__dataclass_fields__}
        ),
    )


def test_matcher_key_exist():
    rules = [_simple_rule("a", key_exist=["toolID"])]
    m = RuleMatcher(rules)
    assert m.match({"toolID": "abc"}) is not None
    assert m.match({"other": "val"}) is None


def test_matcher_not_empty():
    rules = [_simple_rule("a", key_exist=["name"], not_empty=["name"])]
    m = RuleMatcher(rules)
    assert m.match({"name": "hi"}) is not None
    assert m.match({"name": ""}) is None
    assert m.match({"name": None}) is None


def test_matcher_priority():
    low = CardRule(id="low", priority=1, matcher=Matcher(key_exist=["x"]))
    high = CardRule(id="high", priority=10, matcher=Matcher(key_exist=["x"]))
    # load_rules sorts by (-priority, id), so highest-priority comes first
    rules = sorted([low, high], key=lambda r: (-r.priority, r.id))
    m = RuleMatcher(rules)
    assert m.match({"x": 1}).id == "high"


def test_engine_process_returns_unmatched_when_no_rule():
    engine = CardEngine()
    ctx = engine.process({"foo": "bar"}, rule=None)
    assert ctx.rule_id is None
    assert ctx.title == "Unmatched JSON"


def test_engine_formats_template_placeholders():
    engine = CardEngine()
    rule = CardRule(
        id="t",
        matcher=Matcher(key_exist=["name"]),
        render=CardRender(
            title="{name}",
            fields=[],
            timestamp=None,
            badge="{env}",
        ),
    )
    ctx = engine.process({"name": "hello", "env": "prod"}, rule, show_unmapped=False)
    assert ctx.title == "hello"
    assert ctx.badge == "prod"
    assert ctx.unmapped_fields == {}


def test_engine_unmapped_fields_respected():
    engine = CardEngine()
    rule = CardRule(
        id="t",
        matcher=Matcher(key_exist=["a"]),
        render=CardRender(title="t", show_unmapped=True),
    )
    ctx = engine.process({"a": 1, "extra": 2}, rule, show_unmapped=True)
    # Card has no declared fields, so all keys are unmapped
    assert ctx.unmapped_fields == {"a": 1, "extra": 2}


def test_engine_per_card_override_hide_unmapped():
    engine = CardEngine()
    rule = CardRule(
        id="t",
        render=CardRender(title="t", show_unmapped=False),
        matcher=Matcher(key_exist=["a"]),
    )
    ctx = engine.process({"a": 1, "extra": 2}, rule, show_unmapped=True)
    assert ctx.unmapped_fields == {}
