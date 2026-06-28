from __future__ import annotations

import json

from shikari.parsers.models import Finding, ParsedOutput


def parse_json(raw: str) -> ParsedOutput:
    """Parse Semgrep JSON output."""
    parsed = ParsedOutput()
    try:
        data = json.loads(raw)
        results = data.get("results", [])
        for item in results:
            path = item.get("path", "")
            start = item.get("start", {})
            line = start.get("line", 0)
            check_id = item.get("check_id", "")
            extra = item.get("extra", {})
            severity = extra.get("metadata", {}).get("severity", "medium").upper()
            message = extra.get("message", "")
            
            parsed.findings.append(
                Finding(
                    title=f"Semgrep: {check_id}",
                    severity=severity if severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO") else "MEDIUM",
                    target=f"{path}:{line}",
                    description=message,
                    metadata=item,
                )
            )
    except json.JSONDecodeError:
        pass
    return parsed
