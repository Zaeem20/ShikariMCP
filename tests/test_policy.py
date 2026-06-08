"""Tests for local-first safety policy."""

from shikari.config import ShikariConfig, TransportMode
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


def test_metadata_hostname_blocked():
    config = ShikariConfig(enable_active_tools=True, target_allowlist=["*"])
    result = evaluate_tool_policy(
        _tool("nmap_scan"),
        {"target": "metadata.google.internal"},
        config,
    )
    assert result["allowed"] is False
    assert "metadata" in result["reason"].lower()


def test_domain_allowlist_does_not_accept_prefix_confusion():
    config = ShikariConfig(enable_active_tools=True, target_allowlist=["example.com"])
    result = evaluate_tool_policy(
        _tool("nmap_scan"),
        {"target": "example.com.evil.test"},
        config,
    )
    assert result["allowed"] is False


def test_remote_http_blocks_local_scope_even_with_active_flag():
    config = ShikariConfig(
        transport=TransportMode.HTTP,
        local_mode=False,
        enable_active_tools=True,
        enable_remote_active_tools=True,
    )
    result = evaluate_tool_policy(_tool("nmap_scan"), {"target": "example.com"}, config)
    assert result["allowed"] is False
    assert "local-scope" in result["reason"].lower()


def test_remote_http_requires_remote_active_opt_in():
    config = ShikariConfig(
        transport=TransportMode.HTTP,
        local_mode=False,
        enable_active_tools=True,
    )
    result = evaluate_tool_policy(
        _tool("httpx_probe"),
        {"targets": "https://example.com"},
        config,
    )
    assert result["allowed"] is False
    assert "remote http" in result["reason"].lower()


def test_path_allowlist_uses_path_boundaries(tmp_path):
    allowed = tmp_path / "safe"
    sibling = tmp_path / "safe-other" / "input"
    config = ShikariConfig(target_allowlist=[str(allowed)])
    result = evaluate_tool_policy(_tool("trivy_scan"), {"path": str(sibling)}, config)
    assert result["allowed"] is False


def test_auxiliary_wordlist_is_not_treated_as_network_target():
    config = ShikariConfig(
        enable_active_tools=True,
        target_allowlist=["example.com"],
    )
    result = evaluate_tool_policy(
        _tool("ffuf_fuzz"),
        {
            "url": "https://example.com/FUZZ",
            "wordlist": "/opt/wordlists/common.txt",
        },
        config,
    )
    assert result["allowed"] is True
