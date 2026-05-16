from __future__ import annotations

import json

from shikari.parsers.common import severity
from shikari.parsers.models import Evidence, Finding, ParsedOutput


def parse_json(raw: str) -> ParsedOutput:
    parsed = ParsedOutput()
    if not raw.strip():
        return parsed
    data = json.loads(raw)
    for result in data.get("Results", []):
        target = result.get("Target", "")
        for vuln in result.get("Vulnerabilities", []) or []:
            vuln_id = vuln.get("VulnerabilityID", "Vulnerability")
            parsed.findings.append(
                Finding(
                    title=f"{vuln_id}: {vuln.get('PkgName', '')}",
                    severity=severity(vuln.get("Severity")),
                    target=str(target),
                    description=str(vuln.get("Title") or vuln.get("Description") or ""),
                    evidence=[Evidence(source="trivy", value=str(vuln_id), metadata=vuln)],
                    metadata=vuln,
                )
            )
        for misconf in result.get("Misconfigurations", []) or []:
            check_id = misconf.get("ID", "Misconfiguration")
            parsed.findings.append(
                Finding(
                    title=f"{check_id}: {misconf.get('Title', '')}",
                    severity=severity(misconf.get("Severity")),
                    target=str(target),
                    description=str(misconf.get("Description") or ""),
                    evidence=[Evidence(source="trivy", value=str(check_id), metadata=misconf)],
                    metadata=misconf,
                )
            )
    return parsed
