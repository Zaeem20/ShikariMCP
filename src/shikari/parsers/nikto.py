from __future__ import annotations

import json

from shikari.parsers.models import Evidence, Finding, ParsedOutput


def parse_json(raw: str) -> ParsedOutput:
    parsed = ParsedOutput()
    if not raw.strip():
        return parsed
    data = json.loads(raw)
    vulnerabilities = data.get("vulnerabilities") or data.get("items") or []
    for item in vulnerabilities:
        msg = item.get("msg") or item.get("description") or "Nikto finding"
        parsed.findings.append(
            Finding(
                title=str(msg)[:120],
                severity="info",
                target=str(item.get("url") or item.get("host") or ""),
                description=str(msg),
                evidence=[Evidence(source="nikto", value=str(msg), metadata=item)],
                metadata=item,
            )
        )
    return parsed
