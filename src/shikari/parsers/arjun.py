from __future__ import annotations

import json

from shikari.parsers.models import Asset, Finding, ParsedOutput


def parse_json(raw: str) -> ParsedOutput:
    """Parse Arjun parameter mining JSON output."""
    parsed = ParsedOutput()
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            for item in data:
                url = item.get("url", "")
                params = item.get("params", [])
                for param in params:
                    parsed.assets.append(
                        Asset(value=param, type="parameter", source="arjun", metadata={"url": url})
                    )
                if params:
                    parsed.findings.append(
                        Finding(
                            title=f"Arjun: {len(params)} parameter(s) found",
                            severity="INFO",
                            target=url,
                            description=f"Discovered parameters: {', '.join(params[:10])}",
                            metadata=item,
                        )
                    )
    except json.JSONDecodeError:
        pass
    return parsed
