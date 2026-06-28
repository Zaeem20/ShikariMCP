from __future__ import annotations

import re

from shikari.parsers.models import Asset, Endpoint, ParsedOutput


def parse_text(raw: str) -> ParsedOutput:
    """Parse WhatWeb default text output."""
    parsed = ParsedOutput()
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    clean = ansi_escape.sub("", raw)
    for line in clean.splitlines():
        match = re.match(r"^(https?://\S+)\s*\[(\d+[^\]]*)\]\s*(.*)", line)
        if not match:
            continue
        url, status, rest = match.groups()
        technologies = []
        title = ""
        for chunk in re.findall(r"(\w+)\[(.*?)\]", rest):
            name, value = chunk
            if name == "Title":
                title = value.strip("[]")
            technologies.append(name)
        parsed.endpoints.append(
            Endpoint(url=url, title=title, technologies=technologies, metadata={"status": status})
        )
        parsed.assets.append(Asset(value=url, type="url", source="whatweb", metadata={"status": status}))
    return parsed
