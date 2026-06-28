from __future__ import annotations

import json

from shikari.parsers.models import Asset, ParsedOutput, Service


def parse_json(raw: str) -> ParsedOutput:
    """Parse masscan JSON output (-oJ)."""
    parsed = ParsedOutput()
    try:
        data = json.loads(raw)
        if not isinstance(data, list):
            data = [data]
        for item in data:
            ip = item.get("ip")
            if ip:
                parsed.assets.append(Asset(value=str(ip), type="ipv4", source="masscan", metadata=item))
            for port_entry in item.get("ports", []):
                port = port_entry.get("port")
                proto = port_entry.get("proto", "tcp")
                if ip and port is not None:
                    parsed.services.append(
                        Service(
                            host=str(ip),
                            port=int(port),
                            protocol=proto,
                            metadata=port_entry,
                        )
                    )
    except json.JSONDecodeError:
        pass
    return parsed
