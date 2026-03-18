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
