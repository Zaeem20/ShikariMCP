from __future__ import annotations

from shikari.parsers.models import Finding, ParsedOutput


def parse_text(raw: str) -> ParsedOutput:
    """Parse Hydra login check output."""
    parsed = ParsedOutput()
    for line in raw.split("\n"):
        line = line.strip()
        if "login:" in line and "password:" in line:
            # Format: [port][protocol] host: login: X password: Y
            parsed.findings.append(
                Finding(
                    title="Credential found",
                    severity="CRITICAL",
                    target=line.split("login:")[0].strip()[-50:],
                    description=line,
                    metadata={"raw": line},
                )
            )
    return parsed
