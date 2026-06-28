from __future__ import annotations

import json

from shikari.parsers.models import Finding, ParsedOutput


def parse_json(raw: str) -> ParsedOutput:
    """Parse Gitleaks JSON output."""
    parsed = ParsedOutput()
    try:
        data = json.loads(raw)
        if not isinstance(data, list):
            data = [data] if isinstance(data, dict) else []
        for item in data:
            file_path = item.get("File", "")
            line = item.get("StartLine", 0)
            rule = item.get("RuleID", "")
            secret = item.get("Match", "")
            
            parsed.findings.append(
                Finding(
                    title=f"Secret leak: {rule}",
                    severity="CRITICAL",
                    target=f"{file_path}:{line}",
                    description=f"{rule} secret detected. Match: {secret[:50]}...",
                    metadata=item,
                )
            )
    except json.JSONDecodeError:
        pass
    return parsed
