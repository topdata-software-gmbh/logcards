"""Tests for logcards.monolog parsers."""

from logcards.monolog import _level_number, human_datetime, parse_monolog


def test_parse_json_monolog_record():
    record = {
        "message": "ShopIdChangeSuggestedException: Changes in your system",
        "context": {
            "exception": {
                "class": "ShopIdChangeSuggestedException",
                "message": "Changes in your system",
                "code": 0,
            }
        },
        "level": 500,
        "level_name": "CRITICAL",
        "channel": "request",
        "datetime": "2026-09-03T07:15:09.611886+00:00",
        "extra": {},
    }
    result = parse_monolog(record)
    assert result is not None
    assert result["message"] == "ShopIdChangeSuggestedException: Changes in your system"
    assert result["level_name"] == "CRITICAL"
    assert result["level"] == 500
    assert result["channel"] == "request"
    assert result["exception_class"] == "ShopIdChangeSuggestedException"
    assert result["datetime"] == "2026-09-03T07:15:09.611886+00:00"


def test_parse_json_monolog_with_string_exception():
    record = {
        "message": "Something broke",
        "context": {"exception": "[object] (RuntimeException(code: 0): msg"},
        "level": 400,
        "level_name": "ERROR",
        "channel": "request",
    }
    result = parse_monolog(record)
    assert result is not None
    assert result["exception_class"] == "RuntimeException"


def test_parse_json_dict_without_monolog_keys():
    record = {"some_key": "some_value", "count": 42}
    assert parse_monolog(record) is None


def test_parse_symfony_text_line():
    # Real files carry double backslashes in the JSON source; Python needs
    # '\\\\' to produce '\\' in the string.
    line = (
        "[2026-01-15T10:30:00.123456+00:00] request.ERROR: "
        'Uncaught PHP Exception NotFoundHttpException: "No route found" '
        '{"exception":"[object] (Symfony\\\\\\\\Component\\\\\\\\HttpKernel\\\\\\\\Exception\\\\\\\\NotFoundHttpException(code: 0): No route found at RouterListener.php:135)"} []'  # noqa: E501
    )
    result = parse_monolog(line)
    assert result is not None
    assert result["channel"] == "request"
    assert result["level_name"] == "ERROR"
    assert result["level"] == 400
    assert result["exception_class"] == "NotFoundHttpException"
    assert "No route found" in result["message"]


def test_parse_symfony_text_crITICAL():
    line = (
        "[2025-12-29T03:13:18.847106+00:00] console.CRITICAL: "
        'Error thrown while running command "messenger:consume". '
        '{"exception":"[object] (Error(code: 0): Class not found at Kernel.php:36667)"} []'  # noqa: E501
    )
    result = parse_monolog(line)
    assert result is not None
    assert result["channel"] == "console"
    assert result["level_name"] == "CRITICAL"
    assert result["level"] == 500


def test_parse_empty_or_junk_returns_none():
    assert parse_monolog("") is None
    assert parse_monolog("not a log line at all") is None
    assert parse_monolog('{"random": "json"}') is None


def test_human_datetime():
    assert human_datetime("2026-09-03T07:15:09.611886+00:00") == "2026-09-03 07:15:09"
    assert human_datetime("2026-09-03T07:15:09Z") == "2026-09-03 07:15:09"
    assert human_datetime(None) is None
    assert human_datetime("invalid") == "invalid"


def test_level_number_unknown():
    assert _level_number("UNKNOWN_LEVEL") == 0
    assert _level_number("DEBUG") == 100
    assert _level_number("EMERGENCY") == 600
