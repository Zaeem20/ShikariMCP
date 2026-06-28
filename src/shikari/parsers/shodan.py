from __future__ import annotations

import json

from shikari.parsers.models import Asset, Finding, ParsedOutput, Service


def parse_json(raw: str) -> ParsedOutput:
    """Parse Shodan host lookup JSON."""
    parsed = ParsedOutput()
    try:
        data = json.loads(raw)
        ip = data.get("ip_str", "")
        if ip:
            parsed.assets.append(Asset(value=ip, type="ipv4", source="shodan", metadata=data))
        hostnames = data.get("hostnames", [])
        for hostname in hostnames:
            parsed.assets.append(Asset(value=hostname, type="domain", source="shodan", metadata={"ip": ip}))
        for service in data.get("data", []):
            port = service.get("port")
            if port is not None and ip:
                parsed.services.append(
                    Service(
                        host=ip,
                        port=int(port),
                        protocol=service.get("transport", "tcp"),
                        product=service.get("product", ""),
                        version=service.get("version", ""),
                        metadata=service,
                    )
                )
        for cve in data.get("vulns", []):
            parsed.findings.append(
                Finding(
                    title=f"Shodan CVE: {cve}",
                    severity="HIGH",
                    target=ip,
                    description=f"Vulnerability {cve} reported by Shodan",
                    metadata={"cve": cve},
                )
            )
    except json.JSONDecodeError:
        pass
    return parsed
