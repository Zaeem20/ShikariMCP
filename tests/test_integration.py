"""Integration tests using fake binaries to verify tool runner and manifest execution."""

import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from shikari.config import ShikariConfig, set_config
from shikari.core.tool_runner import dry_run_verified_tool, run_verified_tool


@pytest.fixture(scope="module")
def fake_bin_dir():
    tmp = tempfile.mkdtemp()
    tools = [
        "nmap", "subfinder", "httpx", "nuclei", "naabu", "katana",
        "ffuf", "gobuster", "nikto", "sqlmap", "trivy", "whois",
        "masscan", "sslscan", "sslyze", "whatweb", "wafw00f",
        "dnsx", "tlsx", "mapcidr", "uncover", "dalfox", "arjun",
        "semgrep", "gitleaks", "checkov", "yara", "radare2",
        "john", "hashcat", "hydra",
    ]
    for tool in tools:
        script = Path(tmp) / tool
        script.write_text("#!/bin/bash\necho '{\"status\": \"ok\"}'\n")
        script.chmod(0o755)
    yield tmp
    shutil.rmtree(tmp)


@pytest.fixture(autouse=True)
def patch_path(fake_bin_dir):
    old_path = os.environ.get("PATH", "")
    os.environ["PATH"] = f"{fake_bin_dir}:{old_path}"
    yield
    os.environ["PATH"] = old_path


class TestDryRunWithFakeBinaries:
    def test_nmap_dry_run(self):
        result = dry_run_verified_tool("nmap_scan", {"target": "scanme.nmap.org"})
        assert result["tool"]["id"] == "nmap_scan"
        assert "nmap" in result["command"]["argv"][0]
        assert "scanme.nmap.org" in result["command"]["argv"]

    def test_whois_dry_run(self):
        result = dry_run_verified_tool("whois_lookup", {"target": "example.com"})
        assert result["tool"]["id"] == "whois_lookup"
        assert "whois" in result["command"]["argv"][0]
        assert "example.com" in result["command"]["argv"]

    def test_subfinder_dry_run(self):
        result = dry_run_verified_tool("subfinder_enum", {"target": "example.com"})
        assert result["tool"]["id"] == "subfinder_enum"
        assert "subfinder" in result["command"]["argv"][0]

    def test_nuclei_dry_run(self):
        result = dry_run_verified_tool("nuclei_scan", {"target": "https://example.com"})
        assert result["tool"]["id"] == "nuclei_scan"
        assert "nuclei" in result["command"]["argv"][0]

    def test_httpx_dry_run(self):
        result = dry_run_verified_tool("httpx_probe", {"target": "example.com"})
        assert result["tool"]["id"] == "httpx_probe"
        assert "httpx" in result["command"]["argv"][0]

    def test_naabu_dry_run(self):
        result = dry_run_verified_tool("naabu_scan", {"target": "example.com"})
        assert result["tool"]["id"] == "naabu_scan"
        assert "naabu" in result["command"]["argv"][0]

    def test_katana_dry_run(self):
        result = dry_run_verified_tool("katana_crawl", {"target": "https://example.com"})
        assert result["tool"]["id"] == "katana_crawl"
        assert "katana" in result["command"]["argv"][0]

    def test_ffuf_dry_run(self):
        result = dry_run_verified_tool("ffuf_fuzz", {"target": "https://example.com/FUZZ"})
        assert result["tool"]["id"] == "ffuf_fuzz"
        assert "ffuf" in result["command"]["argv"][0]

    def test_gobuster_dry_run(self):
        result = dry_run_verified_tool("gobuster_dir", {"target": "https://example.com"})
        assert result["tool"]["id"] == "gobuster_dir"
        assert "gobuster" in result["command"]["argv"][0]

    def test_nikto_dry_run(self):
        result = dry_run_verified_tool("nikto_scan", {"target": "https://example.com"})
        assert result["tool"]["id"] == "nikto_scan"
        assert "nikto" in result["command"]["argv"][0]

    def test_sqlmap_dry_run(self):
        result = dry_run_verified_tool("sqlmap_scan", {"target": "https://example.com/page?id=1"})
        assert result["tool"]["id"] == "sqlmap_scan"
        assert "sqlmap" in result["command"]["argv"][0]

    def test_trivy_dry_run(self):
        result = dry_run_verified_tool("trivy_scan", {"target": "."})
        assert result["tool"]["id"] == "trivy_scan"
        assert "trivy" in result["command"]["argv"][0]


@pytest.mark.asyncio
class TestRunWithFakeBinaries:
    async def test_whois_run_dry_run_mode(self):
        result = await run_verified_tool("whois_lookup", {"target": "example.com"})
        assert result["status"] == "dry_run"
        assert result["tool"] == "whois_lookup"

    async def test_nmap_blocked_without_active_flag(self):
        set_config(ShikariConfig())
        result = await run_verified_tool(
            "nmap_scan",
            {"target": "scanme.nmap.org"},
            dry_run=False,
        )
        assert result["status"] == "blocked"
        assert "enable-active-tools" in result["errors"][0]

    async def test_run_returns_command_info(self):
        result = await run_verified_tool("httpx_probe", {"target": "example.com"})
        assert result["status"] == "dry_run"
        assert "command" in result
        assert "argv" in result["command"]
