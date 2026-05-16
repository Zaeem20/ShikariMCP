# ShikariMCP - parser helpers

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any


def iter_json_lines(raw: str) -> Iterable[dict[str, Any]]:
    """Yield JSON objects from JSONL output, skipping malformed lines."""
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            yield parsed


def severity(value: str | None) -> str:
    if not value:
        return "info"
    lowered = str(value).lower()
    if lowered in {"critical", "high", "medium", "low", "info"}:
        return lowered
    return "info"
