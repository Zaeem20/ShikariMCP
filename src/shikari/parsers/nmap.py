from __future__ import annotations

import xml.etree.ElementTree as ET

from shikari.parsers.models import Asset, ParsedOutput, Service


def parse_xml(raw: str) -> ParsedOutput:
    parsed = ParsedOutput()
    if not raw.strip():
        return parsed
    root = ET.fromstring(raw)
    for host in root.findall("host"):
        address = host.find("address")
        if address is None:
            continue
        host_value = address.attrib.get("addr", "")
        if not host_value:
            continue
        parsed.assets.append(Asset(value=host_value, type=address.attrib.get("addrtype", "host"), source="nmap"))
        for port in host.findall("./ports/port"):
            state = port.find("state")
            if state is not None and state.attrib.get("state") not in {"open", "open|filtered"}:
                continue
            service = port.find("service")
            parsed.services.append(
                Service(
                    host=host_value,
                    port=int(port.attrib.get("portid", "0")),
                    protocol=port.attrib.get("protocol", "tcp"),
                    name=service.attrib.get("name", "") if service is not None else "",
                    product=service.attrib.get("product", "") if service is not None else "",
                    version=service.attrib.get("version", "") if service is not None else "",
                    metadata={"state": state.attrib if state is not None else {}},
                )
            )
    return parsed
