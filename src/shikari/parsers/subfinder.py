from __future__ import annotations

from shikari.parsers.common import iter_json_lines
from shikari.parsers.models import Asset, ParsedOutput


def parse_jsonl(raw: str) -> ParsedOutput:
    parsed = ParsedOutput()
    for item in iter_json_lines(raw):
        host = item.get("host") or item.get("input") or item.get("domain")
        if host:
            parsed.assets.append(Asset(value=str(host), type="domain", source="subfinder", metadata=item))
    if not parsed.assets:
        for line in raw.splitlines():
            host = line.strip()
            if host:
                parsed.assets.append(Asset(value=host, type="domain", source="subfinder"))
    return parsed
