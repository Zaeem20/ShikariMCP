from __future__ import annotations

import json

from shikari.parsers.models import Finding, ParsedOutput


def parse_jsonl(raw: str) -> ParsedOutput:
    """Parse Dalfox JSONL output."""
    parsed = ParsedOutput()
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
            vuln_type = item.get("type", "")
            severity = item.get("severity", "high").upper()
            target = item.get("data", {}).get("payload", "")
            message = item.get("data", {}).get("message", "")
            
            parsed.findings.append(
                Finding(
                    title=f"XSS: {vuln_type}",
                    severity=severity if severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO") else "HIGH",
                    target=target,
                    description=message,
                    metadata=item,
                )
            )
        except json.JSONDecodeError:
            continue
    return parsed
