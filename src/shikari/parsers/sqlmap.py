from __future__ import annotations

from shikari.parsers.models import Evidence, Finding, ParsedOutput


def parse_text(raw: str) -> ParsedOutput:
    parsed = ParsedOutput()
    lowered = raw.lower()
    if "is vulnerable" in lowered or "parameter" in lowered and "injectable" in lowered:
        parsed.findings.append(
            Finding(
                title="Potential SQL injection",
                severity="high",
                description="SQLMap output indicates an injectable parameter.",
                evidence=[Evidence(source="sqlmap", value=raw[:2000])],
            )
        )
    return parsed
