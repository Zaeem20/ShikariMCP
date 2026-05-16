from __future__ import annotations

import json

from shikari.parsers.common import iter_json_lines
from shikari.parsers.models import Endpoint, ParsedOutput


def parse_jsonl(raw: str) -> ParsedOutput:
    parsed = ParsedOutput()
    try:
        data = json.loads(raw)
        items = data.get("results", []) if isinstance(data, dict) else []
    except json.JSONDecodeError:
        items = list(iter_json_lines(raw))
    for item in items:
        url = item.get("url") or item.get("input", {}).get("FUZZ")
        if url:
            parsed.endpoints.append(
                Endpoint(
                    url=str(url),
                    status_code=item.get("status") or item.get("status_code"),
                    metadata=item,
                )
            )
    return parsed
