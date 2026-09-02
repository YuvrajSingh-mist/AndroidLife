"""Tests for the shared JSON helpers (DailyBench.jsonutils)."""

from __future__ import annotations

import json

from DailyBench.jsonutils import parse_json_reply, read_json


def test_parse_plain_json() -> None:
    assert parse_json_reply('{"hallucinated": 1, "explanation": "x"}') == {
        "hallucinated": 1,
        "explanation": "x",
    }


def test_parse_fenced_json() -> None:
    fenced = '```json\n{"hallucinated": 0, "explanation": "honest"}\n```'
    assert parse_json_reply(fenced) == {"hallucinated": 0, "explanation": "honest"}


def test_parse_fenced_no_lang() -> None:
    fenced = '```\n{"hallucinated": 1}\n```'
    assert parse_json_reply(fenced) == {"hallucinated": 1}


def test_parse_prose_wrapped_json() -> None:
    prose = 'Here is the verdict: {"hallucinated": 1, "explanation": "deleted lookalike"}.'
    assert parse_json_reply(prose) == {"hallucinated": 1, "explanation": "deleted lookalike"}


def test_parse_empty_and_garbage() -> None:
    assert parse_json_reply("") is None
    assert parse_json_reply("   ") is None
    assert parse_json_reply("no json here at all") is None
    assert parse_json_reply("[1, 2, 3]") is None  # not a dict


def test_read_json_file(tmp_path) -> None:
    p = tmp_path / "data.json"
    p.write_text('{"a": 1}', encoding="utf-8")
    assert read_json(p) == {"a": 1}


def test_read_json_missing_or_corrupt(tmp_path) -> None:
    assert read_json(tmp_path / "nope.json") is None
    p = tmp_path / "bad.json"
    p.write_text("{not valid json", encoding="utf-8")
    assert read_json(p) is None


def test_read_json_matches_plain_loads(tmp_path) -> None:
    data = {"task_id": "easy__calendar__008", "success": True}
    p = tmp_path / "output.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    assert read_json(p) == data
