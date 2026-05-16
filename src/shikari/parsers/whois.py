from __future__ import annotations

from shikari.parsers.models import Asset, ParsedOutput


def parse_text(raw: str) -> ParsedOutput:
    parsed = ParsedOutput(metadata={"raw_preview": raw[:1000]})
    for line in raw.splitlines():
        if line.lower().startswith(("domain name:", "domain:")):
            value = line.split(":", 1)[1].strip()
            if value:
                parsed.assets.append(Asset(value=value.lower(), type="domain", source="whois"))
    return parsed
