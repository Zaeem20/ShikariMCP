from __future__ import annotations

import json

from shikari.parsers.models import Finding, ParsedOutput


def parse_json(raw: str) -> ParsedOutput:
    """Parse Checkov JSON output."""
    parsed = ParsedOutput()
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            for item in data:
                resource = item.get("resource", "")
                check_id = item.get("check_id", "")
                check_name = item.get("check_name", "")
                severity = item.get("severity", "MEDIUM").upper()
                file_path = item.get("file_path", "")
                
                parsed.findings.append(
                    Finding(
                        title=f"Checkov: {check_name}",
                        severity=severity if severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO") else "MEDIUM",
                        target=f"{file_path} — {resource}",
                        description=f"{check_id}: {check_name}",
                        metadata=item,
                    )
                )
        elif isinstance(data, dict):
            # Checkov sometimes returns wrapped results
            for framework, results in data.items():
                if isinstance(results, list):
                    for item in results:
                        parsed.findings.append(
                            Finding(
                                title=f"Checkov: {item.get('check_name', 'Unknown')}",
                                severity=item.get("severity", "MEDIUM").upper(),
                                target=f"{framework} — {item.get('resource', '')}",
                                description=f"{item.get('check_id', '')}: {item.get('check_name', '')}",
                                metadata=item,
                            )
                        )
    except json.JSONDecodeError:
        pass
    return parsed
