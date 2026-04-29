# ShikariMCP — Output Parsing Utilities

import json
import re
import logging
from typing import Any

logger = logging.getLogger("shikari.parser")


def parse_json_output(raw: str) -> dict | list | None:
    """Attempt to parse JSON from tool output."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract JSON from mixed output
        json_match = re.search(r"[\[{].*[}\]]", raw, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
    return None


def parse_table_output(raw: str) -> list[dict[str, str]]:
    """Parse tabular output (space-separated columns with header)."""
    lines = [line.strip() for line in raw.strip().splitlines() if line.strip()]
    if len(lines) < 2:
        return []

    headers = lines[0].split()
    results = []
    for line in lines[1:]:
        values = line.split(None, len(headers) - 1)
        row = {}
        for i, header in enumerate(headers):
            row[header] = values[i] if i < len(values) else ""
        results.append(row)

    return results


def format_tool_result(
    tool_name: str,
    result: Any,
    success: bool = True,
) -> str:
    """Format a tool result into a clean, readable string."""
    if isinstance(result, dict):
        return json.dumps(result, indent=2)
    if isinstance(result, list):
        return json.dumps(result, indent=2)
    return str(result)


def truncate_output(output: str, max_chars: int = 50000) -> str:
    """Truncate output to prevent overwhelming the LLM context."""
    if len(output) <= max_chars:
        return output
    half = max_chars // 2
    return (
        output[:half]
        + f"\n\n--- [TRUNCATED: {len(output) - max_chars} chars omitted] ---\n\n"
        + output[-half:]
    )


def extract_security_findings(raw: str, source: str = "tool") -> list[dict[str, str]]:
    """Extract lightweight findings from common security tool output."""
    findings: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for line in raw.splitlines():
        normalized = line.strip()
        if not normalized:
            continue
        lower = normalized.lower()
        severity = ""
        if "critical" in lower:
            severity = "CRITICAL"
        elif "high" in lower:
            severity = "HIGH"
        elif "medium" in lower:
            severity = "MEDIUM"
        elif "low" in lower:
            severity = "LOW"
        elif re.search(r"\bopen\b", lower) and "/tcp" in lower:
            severity = "INFO"
        elif "cve-" in lower or "vulnerab" in lower:
            severity = "MEDIUM"

        if not severity:
            continue

        cve_match = re.search(r"CVE-\d{4}-\d{4,7}", normalized, re.IGNORECASE)
        title = cve_match.group(0).upper() if cve_match else f"{source} signal"
        key = (title, normalized)
        if key in seen:
            continue
        seen.add(key)
        findings.append({"severity": severity, "title": title, "detail": normalized})

    return findings
