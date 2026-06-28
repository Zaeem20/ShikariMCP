from __future__ import annotations

from shikari.parsers.models import Asset, Finding, ParsedOutput


def parse_text(raw: str) -> ParsedOutput:
    """Parse John the Ripper crack output."""
    parsed = ParsedOutput()
    for line in raw.split("\n"):
        line = line.strip()
        if not line or line.startswith("Using") or line.startswith("Warning"):
            continue
        # Format: "username:password:uid:gid:..." or "hash:password"
        if ":" in line and not line.startswith("No password"):
            parts = line.split(":", 1)
            if len(parts) == 2:
                user_or_hash = parts[0]
                password = parts[1]
                parsed.findings.append(
                    Finding(
                        title="Password cracked",
                        severity="CRITICAL",
                        target=user_or_hash[:50],
                        description=f"Password recovered: {password[:20]}...",
                        metadata={"user": user_or_hash, "password": password},
                    )
                )
                parsed.assets.append(
                    Asset(value=user_or_hash, type="credential", source="john", metadata={"cracked": True})
                )
    return parsed
