from __future__ import annotations

import json

from shikari.parsers.models import Finding, ParsedOutput


def parse_json(raw: str) -> ParsedOutput:
    parsed = ParsedOutput()
    if not raw.strip():
        return parsed

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return parsed

    # Extract the data dict; could be top-level key or the whole object
    obj = data if isinstance(data, dict) else {}
    if not obj:
        return parsed

    # Sometimes VT wraps in a "data" key
    inner = obj.get("data") or obj
    if isinstance(inner, dict):
        resource_id = inner.get("id") or obj.get("id") or ""
    else:
        resource_id = ""

    attributes = (inner.get("attributes") if isinstance(inner, dict) else obj.get("attributes")) or {}
    stats = attributes.get("last_analysis_stats") or {}

    malicious = int(stats.get("malicious") or 0)
    suspicious = int(stats.get("suspicious") or 0)
    harmless = int(stats.get("harmless") or 0)
    undetected = int(stats.get("undetected") or 0)

    if not resource_id:
        return parsed

    parsed.findings.append(
        Finding(
            title=f"VirusTotal: {resource_id} — {malicious} malicious, {suspicious} suspicious",
            severity="high" if malicious > 0 else "info",
            target=resource_id,
            description=f"Analysis stats: malicious={malicious}, suspicious={suspicious}, harmless={harmless}, undetected={undetected}",
            metadata=data,
        )
    )

    return parsed
