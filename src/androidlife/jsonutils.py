"""Shared JSON parsing helpers for LLM replies and file reads"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def parse_json_reply(content: str) -> dict[str, Any] | None:
    """Best-effort parse of an LLM reply that should be a single JSON object.

    Handles the common failure modes of chat-completion JSON output:
    - ```json ... ``` markdown fences (with or without the language tag)
    - leading/trailing prose around the object
    - a valid JSON object embedded anywhere in the text

    Returns the parsed ``dict`` when one is found, else ``None`` (never raises).
    """
    if not content:
        return None
    text = content.strip()
    if text.startswith("```"):
        # strip ```json ... ``` fences
        lines = text.splitlines()
        lines = [ln for ln in lines if not ln.strip().startswith("```")]
        text = "\n".join(lines).strip()
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except Exception:
        # last-ditch: find the first {...} block
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            return None
        try:
            obj = json.loads(m.group(0))
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None


def read_json(path: str | Path) -> Any | None:
    """Read + parse a JSON file. Returns ``None`` on missing file / parse error."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
