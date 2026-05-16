from __future__ import annotations

from shikari.parsers.common import iter_json_lines
from shikari.parsers.models import Endpoint, ParsedOutput


def parse_jsonl(raw: str) -> ParsedOutput:
    parsed = ParsedOutput()
    for item in iter_json_lines(raw):
        url = item.get("url") or item.get("request", {}).get("endpoint")
        if url:
            parsed.endpoints.append(Endpoint(url=str(url), metadata=item))
    if not parsed.endpoints:
        for line in raw.splitlines():
            url = line.strip()
            if url.startswith(("http://", "https://")):
                parsed.endpoints.append(Endpoint(url=url))
    return parsed
