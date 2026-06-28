from __future__ import annotations

import json

from shikari.parsers.models import Finding, ParsedOutput


def parse_json(raw: str) -> ParsedOutput:
    """Parse wafw00f JSON output."""
    parsed = ParsedOutput()
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            for item in data:
                detected = item.get("detected", False)
                firewall = item.get("firewall", "Unknown")
                url = item.get("url", "")
                if detected:
                    parsed.findings.append(
                        Finding(
                            title=f"WAF detected: {firewall}",
                            severity="INFO",
                            target=url,
                            description=f"{firewall} Web Application Firewall detected on {url}",
                            metadata=item,
                        )
                    )
    except json.JSONDecodeError:
        pass
    return parsed
