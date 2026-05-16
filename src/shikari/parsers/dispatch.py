# ShikariMCP - parser dispatch

from __future__ import annotations

import importlib

from shikari.parsers.models import ParsedOutput


def parse_tool_output(parser_ref: str | None, raw: str) -> ParsedOutput:
    """Load and run a parser by dotted reference."""
    if not parser_ref:
        return ParsedOutput()
    module_name, func_name = parser_ref.rsplit(".", 1)
    module = importlib.import_module(module_name)
    parser = getattr(module, func_name)
    parsed = parser(raw)
    if isinstance(parsed, ParsedOutput):
        return parsed
    return ParsedOutput.model_validate(parsed)
