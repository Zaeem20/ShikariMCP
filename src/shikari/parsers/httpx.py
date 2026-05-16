from __future__ import annotations

from shikari.parsers.common import iter_json_lines
from shikari.parsers.models import Endpoint, ParsedOutput


def parse_jsonl(raw: str) -> ParsedOutput:
    parsed = ParsedOutput()
    for item in iter_json_lines(raw):
        url = item.get("url") or item.get("input")
        if not url:
            continue
        tech = item.get("tech") or item.get("technologies") or []
        if isinstance(tech, str):
            tech = [tech]
        parsed.endpoints.append(
            Endpoint(
                url=str(url),
                status_code=item.get("status_code"),
                title=str(item.get("title") or ""),
                technologies=[str(value) for value in tech],
                metadata=item,
            )
        )
    return parsed
