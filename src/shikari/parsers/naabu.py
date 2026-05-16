from __future__ import annotations

from shikari.parsers.common import iter_json_lines
from shikari.parsers.models import Asset, ParsedOutput, Service


def parse_jsonl(raw: str) -> ParsedOutput:
    parsed = ParsedOutput()
    for item in iter_json_lines(raw):
        host = item.get("host") or item.get("ip") or item.get("timestamp")
        port = item.get("port")
        if host:
            parsed.assets.append(Asset(value=str(host), type="host", source="naabu", metadata=item))
        if host and port is not None:
            parsed.services.append(Service(host=str(host), port=int(port), protocol="tcp", metadata=item))
    return parsed
