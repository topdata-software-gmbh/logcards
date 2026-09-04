"""Tests for the terminal renderer."""

from logcards.engine import CardEngine
from logcards.renderers.terminal import TerminalCardRenderer
from logcards.rules import CardField, CardRender, CardRule, Matcher, Payload


def test_render_card_returns_panel():
    rule = CardRule(
        id="test",
        matcher=Matcher(key_exist=["x"]),
        render=CardRender(
            title="Hello",
            border="cyan",
            badge="env:prod",
            fields=[CardField(key="x", value="{x}")],
            payload=Payload(source="data", formatter="json"),
        ),
    )
    engine = CardEngine()
    renderer = TerminalCardRenderer(theme="monokai")
    ctx = engine.process({"x": "val", "data": {"k": 1}}, rule, show_unmapped=True)
    panel = renderer.render(ctx, {"x": "val"})
    assert panel.title == "Hello [reverse] env:prod [/]"


def test_render_unmatched_returns_json_syntax_panel():
    engine = CardEngine()
    renderer = TerminalCardRenderer()
    ctx = engine.process({"foo": "bar"}, rule=None)
    panel = renderer.render(ctx, {"foo": "bar"})
    assert panel.title == "📄 [dim]Unmatched JSON[/dim]"
