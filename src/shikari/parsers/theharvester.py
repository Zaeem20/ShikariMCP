from __future__ import annotations

import re

from shikari.parsers.models import Asset, ParsedOutput

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def _classify_line(text: str) -> str | None:
    """Return 'email', 'host', 'url', or None based on content heuristics."""
    if _EMAIL_RE.match(text):
        return "email"
    if text.startswith("http://") or text.startswith("https://"):
        return "url"
    if re.match(r"^[\w.-]+\.[a-z]{2,}(?::\d+)?$", text, re.IGNORECASE):
        return "host"
    return None


def parse_text(raw: str) -> ParsedOutput:
    parsed = ParsedOutput()
    if not raw.strip():
        return parsed

    current_section: str | None = None
    section_map: dict[str, str] = {
        "emails": "email",
        "hosts": "host",
        "urls": "url",
        "users": "user",
    }

    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue

        # Detect section headers like "[*] Emails found:"
        section_match = re.match(r"\[\*\]\s*(.+?)\s*found:", line, re.IGNORECASE)
        if section_match:
            section_name = section_match.group(1).strip().lower()
            current_section = section_map.get(section_name)
            continue

        # Also detect "─────" style separators
        if re.match(r"^[─\-=]{3,}$", line):
            continue

        # Classify by section context
        asset_type = current_section
        if not asset_type:
            asset_type = _classify_line(line)

        if asset_type == "email":
            if _EMAIL_RE.match(line):
                parsed.assets.append(
                    Asset(value=line, type="email", source="theharvester")
                )
        elif asset_type == "host":
            # Strip trailing port for the value
            host_value = line.split(":")[0] if ":" in line else line
            parsed.assets.append(
                Asset(value=host_value, type="host", source="theharvester")
            )
        elif asset_type == "url":
            parsed.assets.append(
                Asset(value=line, type="url", source="theharvester")
            )

    # Fallback: scan entire output for emails via regex
    for match in _EMAIL_RE.finditer(raw):
        email = match.group(0)
        # Avoid duplicates — check if already added
        if not any(a.value == email and a.type == "email" for a in parsed.assets):
            parsed.assets.append(
                Asset(value=email, type="email", source="theharvester")
            )

    return parsed
