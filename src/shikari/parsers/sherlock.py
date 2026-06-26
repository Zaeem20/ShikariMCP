from __future__ import annotations

import csv
import io

from shikari.parsers.models import Asset, Finding, ParsedOutput


def parse_csv(raw: str) -> ParsedOutput:
    parsed = ParsedOutput()
    if not raw.strip():
        return parsed

    try:
        reader = csv.DictReader(io.StringIO(raw))
    except Exception:
        return parsed

    for row in reader:
        try:
            http_status_str = (row.get("http_status") or "").strip()
            http_status = int(http_status_str) if http_status_str.isdigit() else None
        except (ValueError, TypeError):
            http_status = None

        if http_status not in (200, 301, 302, 403):
            continue

        site = (row.get("site") or "").strip()
        url = (row.get("url") or "").strip()
        username = (row.get("username") or "").strip()

        if not site or not url:
            continue

        parsed.assets.append(
            Asset(
                value=url,
                type="social_profile",
                source="sherlock",
                metadata=dict(row),
            )
        )
        parsed.findings.append(
            Finding(
                title=f"Profile found on {site}",
                severity="info",
                target=username,
                description=f"Username '{username}' found on {site}: {url}",
            )
        )

    return parsed
