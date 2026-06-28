from __future__ import annotations

from shikari.parsers.models import Asset, Finding, ParsedOutput


def parse_text(raw: str) -> ParsedOutput:
    """Parse Hashcat crack output."""
    parsed = ParsedOutput()
    for line in raw.split("\n"):
        line = line.strip()
        if not line or line.startswith("hashcat") or line.startswith("OpenCL") or line.startswith("CUDA"):
            continue
        # Format: "hash:password" or "hash:plain"
        if ":" in line:
            parts = line.split(":", 1)
            if len(parts) == 2:
                hash_val = parts[0]
                password = parts[1]
                parsed.findings.append(
                    Finding(
                        title="Hash cracked",
                        severity="CRITICAL",
                        target=hash_val[:50],
                        description=f"Password recovered: {password[:20]}...",
                        metadata={"hash": hash_val, "password": password},
                    )
                )
                parsed.assets.append(
                    Asset(value=hash_val, type="hash", source="hashcat", metadata={"cracked": True})
                )
    return parsed
