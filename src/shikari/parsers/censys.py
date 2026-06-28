from __future__ import annotations

import json

from shikari.parsers.models import Asset, ParsedOutput, Service


def parse_json(raw: str) -> ParsedOutput:
    """Parse Censys host view JSON."""
    parsed = ParsedOutput()
    if not raw.strip():
        return parsed

    if "no api id or secret configured" in raw.lower() or "censysapiexception" in raw.lower():
        parsed.errors.append("Censys API credentials not found. Set CENSYS_API_ID and CENSYS_API_SECRET.")
        return parsed

    try:
        data = json.loads(raw)
        ip = data.get("ip", "")
        if ip:
            parsed.assets.append(Asset(value=str(ip), type="ipv4", source="censys", metadata=data))
        for svc in data.get("services", []):
            port = svc.get("port")
            if port is not None and ip:
                parsed.services.append(
                    Service(
                        host=str(ip),
                        port=int(port),
                        protocol=svc.get("transport_protocol", "tcp").lower(),
                        product=svc.get("service_name", ""),
                        version=svc.get("software", [{}])[0].get("version", "") if svc.get("software") else "",
                        metadata=svc,
                    )
                )
    except json.JSONDecodeError:
        pass
    return parsed
