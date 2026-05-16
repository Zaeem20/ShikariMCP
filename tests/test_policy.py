"""Tests for local-first safety policy."""

from shikari.config import ShikariConfig
from shikari.core.policy import evaluate_tool_policy
from shikari.core.tool_manifest import load_tool_manifest


def _tool(tool_id: str):
    manifest = load_tool_manifest("core")
    return next(tool for tool in manifest.tools if tool.id == tool_id)


def test_active_tool_blocked_by_default():
    result = evaluate_tool_policy(_tool("nmap_scan"), {"target": "example.com"}, ShikariConfig())
    assert result["allowed"] is False
    assert "enable-active-tools" in result["reason"]


def test_active_tool_allowed_with_flag():
    config = ShikariConfig(enable_active_tools=True)
    result = evaluate_tool_policy(_tool("nmap_scan"), {"target": "example.com"}, config)
    assert result["allowed"] is True


def test_target_allowlist_blocks_unknown_target():
    config = ShikariConfig(enable_active_tools=True, target_allowlist=["example.com"])
    result = evaluate_tool_policy(_tool("nmap_scan"), {"target": "evil.test"}, config)
    assert result["allowed"] is False
    assert "ALLOWLIST" in result["reason"]


def test_metadata_ip_blocked():
    config = ShikariConfig(enable_active_tools=True, target_allowlist=["*"])
    result = evaluate_tool_policy(_tool("nmap_scan"), {"target": "169.254.169.254"}, config)
    assert result["allowed"] is False
    assert "metadata" in result["reason"].lower()
