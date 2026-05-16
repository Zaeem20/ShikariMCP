"""Tests for manifest-driven tool command building."""

import pytest

from shikari.config import ShikariConfig, set_config
from shikari.core.tool_runner import dry_run_verified_tool, run_verified_tool


def test_dry_run_builds_nmap_command():
    result = dry_run_verified_tool("nmap_scan", {"target": "scanme.nmap.org"})

    assert result["tool"]["id"] == "nmap_scan"
    assert result["command"]["argv"] == [
        "nmap",
        "-oX",
        "-",
        "-sV",
        "--version-light",
        "--reason",
        "scanme.nmap.org",
    ]
    assert result["approval"] == "active_tools"


def test_dry_run_reports_missing_input():
    with pytest.raises(ValueError, match="Missing required input"):
        dry_run_verified_tool("nmap_scan", {})


@pytest.mark.asyncio
async def test_run_verified_tool_defaults_to_dry_run():
    result = await run_verified_tool("whois_lookup", {"target": "example.com"})

    assert result["status"] == "dry_run"
    assert result["tool"] == "whois_lookup"
    assert result["command"]["argv"] == ["whois", "example.com"]


@pytest.mark.asyncio
async def test_run_verified_tool_blocks_active_without_flag():
    set_config(ShikariConfig())
    result = await run_verified_tool(
        "nmap_scan",
        {"target": "scanme.nmap.org"},
        dry_run=False,
    )

    assert result["status"] == "blocked"
    assert "enable-active-tools" in result["errors"][0]
