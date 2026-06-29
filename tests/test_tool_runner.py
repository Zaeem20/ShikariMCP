"""Tests for manifest-driven tool command building."""

import pytest

from shikari.config import ShikariConfig, set_config
from shikari.core.tool_runner import dry_run_tool, run_tool


def test_dry_run_builds_nmap_command():
    result = dry_run_tool("nmap_scan", {"target": "scanme.nmap.org"})

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
        dry_run_tool("nmap_scan", {})


def test_common_target_aliases_are_normalized():
    httpx = dry_run_tool("httpx_probe", {"target": "https://example.com"})
    trivy = dry_run_tool("trivy_scan", {"target": "."})
    ffuf = dry_run_tool(
        "ffuf_fuzz",
        {"target": "https://example.com/FUZZ"},
    )

    assert httpx["command"]["stdin"] == "https://example.com"
    assert trivy["command"]["argv"][-1] == "."
    assert ffuf["command"]["argv"][2] == "https://example.com/FUZZ"
    assert "-w" in ffuf["command"]["argv"]


def test_input_option_prefix_is_rejected():
    with pytest.raises(ValueError, match="option prefix"):
        dry_run_tool("nmap_scan", {"target": "--script=unsafe"})


def test_output_file_is_allocated_for_file_output():
    result = dry_run_tool("nikto_scan", {"target": "https://example.com"})
    output_index = result["command"]["argv"].index("-output") + 1
    assert result["command"]["argv"][output_index].endswith(".json")


def test_output_file_cannot_escape_artifact_directory(tmp_path):
    outside = tmp_path / "outside.json"
    result = dry_run_tool(
        "nikto_scan",
        {
            "target": "https://example.com",
            "output_file": str(outside),
        },
    )
    output_index = result["command"]["argv"].index("-output") + 1
    assert result["command"]["argv"][output_index] != str(outside)


@pytest.mark.asyncio
async def test_run_tool_dry_run_preview():
    result = await run_tool("whois_lookup", {"target": "example.com"}, dry_run=True)

    assert result["status"] == "dry_run"
    assert result["tool"] == "whois_lookup"
    assert result["command"]["argv"] == ["whois", "example.com"]


@pytest.mark.asyncio
async def test_run_tool_defaults_to_execute():
    """run_tool() should default to dry_run=False (actually execute)."""
    result = await run_tool("whois_lookup", {"target": "example.com"})
    assert result["status"] != "dry_run"


@pytest.mark.asyncio
async def test_run_tool_allows_active_by_default():
    set_config(ShikariConfig(enable_active_tools=True))
    result = await run_tool(
        "nmap_scan",
        {"target": "scanme.nmap.org"},
        dry_run=False,
    )

    # Policy should allow it (not blocked); actual execution may fail if
    # the nmap binary is not installed on the test machine.
    assert result["status"] != "blocked"
    assert result["status"] in {"success", "failed", "degraded"}


@pytest.mark.asyncio
async def test_run_tool_blocks_active_when_disabled():
    set_config(ShikariConfig(enable_active_tools=False))
    result = await run_tool(
        "nmap_scan",
        {"target": "scanme.nmap.org"},
        dry_run=False,
    )

    assert result["status"] == "blocked"
    assert "enable-active-tools" in result["errors"][0]
