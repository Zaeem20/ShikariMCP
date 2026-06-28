from __future__ import annotations

import json

from shikari.parsers.models import Asset, Finding, ParsedOutput


def parse_json(raw: str) -> ParsedOutput:
    parsed = ParsedOutput()
    if not raw.strip():
        return parsed

    if "api key not found" in raw.lower():
        parsed.errors.append("GreyNoise API key not found. Set GREYNOISE_API_KEY or run 'greynoise setup'.")
        return parsed

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return parsed

    if not isinstance(data, list):
        data = [data]

    for item in data:
        if not isinstance(item, dict):
            continue

        ip = item.get("ip") or ""
        if not ip:
            continue

        classification = str(item.get("classification") or "unknown")
        actor = item.get("actor") or ""
        tags = item.get("tags") or []
        first_seen = item.get("first_seen") or ""

        parsed.assets.append(
            Asset(
                value=str(ip),
                type="ip",
                source="greynoise",
                metadata=item,
            )
        )

        parsed.findings.append(
            Finding(
                title=f"GreyNoise: {ip} classified as {classification}",
                severity="high" if classification == "malicious" else "info",
                target=str(ip),
                description=f"Actor: {actor}, Tags: {tags}, First seen: {first_seen}",
                metadata=item,
            )
        )

    return parsed
