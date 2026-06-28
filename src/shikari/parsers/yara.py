from __future__ import annotations

from shikari.parsers.models import Finding, ParsedOutput


def parse_text(raw: str) -> ParsedOutput:
    """Parse YARA scan text output."""
    parsed = ParsedOutput()
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        # YARA output format: "rule_name file_path" or "rule_name [meta]"
        if line.startswith("warning"):
            continue
        parts = line.split(None, 1)
        if len(parts) >= 1 and not line.startswith(" "):
            rule_name = parts[0]
            file_path = parts[1] if len(parts) > 1 else ""
            parsed.findings.append(
                Finding(
                    title=f"YARA match: {rule_name}",
                    severity="HIGH",
                    target=file_path,
                    description=f"File matched YARA rule: {rule_name}",
                    metadata={"rule": rule_name, "file": file_path},
                )
            )
    return parsed
