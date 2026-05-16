from __future__ import annotations

import re

from shikari.parsers.models import Endpoint, ParsedOutput

STATUS_RE = re.compile(r"(?P<path>/\S+).*Status:\s*(?P<status>\d+)")


def parse_text(raw: str) -> ParsedOutput:
    parsed = ParsedOutput()
    for line in raw.splitlines():
        match = STATUS_RE.search(line)
        if match:
            parsed.endpoints.append(
                Endpoint(
                    url=match.group("path"),
                    status_code=int(match.group("status")),
                    metadata={"raw": line},
                )
            )
    return parsed
