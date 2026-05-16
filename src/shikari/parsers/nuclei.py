from __future__ import annotations

from shikari.parsers.common import iter_json_lines, severity
from shikari.parsers.models import Evidence, Finding, ParsedOutput


def parse_jsonl(raw: str) -> ParsedOutput:
    parsed = ParsedOutput()
    for item in iter_json_lines(raw):
        info = item.get("info") or {}
        title = info.get("name") or item.get("template-id") or "Nuclei finding"
        target = item.get("matched-at") or item.get("host") or item.get("url") or ""
        parsed.findings.append(
            Finding(
                title=str(title),
                severity=severity(info.get("severity")),
                target=str(target),
                description=str(info.get("description") or ""),
                evidence=[Evidence(source="nuclei", value=str(target), metadata=item)],
                metadata={
                    "template_id": item.get("template-id"),
                    "matcher_name": item.get("matcher-name"),
                    "type": item.get("type"),
                },
            )
        )
    return parsed
