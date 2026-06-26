"""Tests for verified tool manifests."""

from types import SimpleNamespace

from shikari.core import tool_manifest


def test_core_manifest_loads():
    manifest = tool_manifest.load_tool_manifest("core")

    assert manifest.profile == "core"
    assert manifest.schema_version == 1
    assert len(manifest.tools) >= 10
    assert {tool.id for tool in manifest.tools} >= {
        "nmap_scan",
        "subfinder_enum",
        "httpx_probe",
        "nuclei_scan",
        "trivy_scan",
    }


def test_public_catalog_has_no_runtime_checks():
    catalog = tool_manifest.manifest_public_catalog("core")

    assert catalog["profile"] == "core"
    assert catalog["tools"]
    assert "version_output" not in catalog["tools"][0]


def test_explain_tool_by_id_and_binary():
    by_id = tool_manifest.explain_tool("nmap_scan")
    by_binary = tool_manifest.explain_tool("nmap")

    assert by_id["tool"]["id"] == "nmap_scan"
    assert by_binary["tool"]["id"] == "nmap_scan"
    assert by_id["safe_templates"]["safe"]["output_format"] == "xml"
    assert any("active network" in note.lower() for note in by_id["notes"])


def test_verify_profile_reports_missing_binary(monkeypatch):
    monkeypatch.setattr(tool_manifest.shutil, "which", lambda binary: None)

    result = tool_manifest.verify_tool_profile("core")

    assert result["total"] >= 10
    assert result["installed"] == 0
    assert result["missing"] == result["total"]
    assert result["tools"][0]["error"] == "binary not found on PATH"


def test_verify_profile_runs_version_command(monkeypatch):
    monkeypatch.setattr(tool_manifest.shutil, "which", lambda binary: f"/usr/bin/{binary}")

    def fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=0, stdout="tool version 1.0", stderr="")

    monkeypatch.setattr(tool_manifest.subprocess, "run", fake_run)

    result = tool_manifest.verify_tool_profile("core")

    assert result["installed"] == result["total"]
    assert result["version_ok"] == result["total"]
    assert result["tools"][0]["version_output"] == "tool version 1.0"


def test_verify_accepts_nonzero_exit_with_output(monkeypatch):
    """Tools like hydra exit non-zero for --help but still print help text."""
    monkeypatch.setattr(tool_manifest.shutil, "which", lambda binary: f"/usr/bin/{binary}")

    def fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr="hydra 9.5")

    monkeypatch.setattr(tool_manifest.subprocess, "run", fake_run)

    result = tool_manifest.verify_tool_profile("core")

    assert result["installed"] == result["total"]
    assert result["version_ok"] == result["total"]


def test_verify_rejects_nonzero_exit_no_output(monkeypatch):
    """A binary that exits non-zero with no output is genuinely broken."""
    monkeypatch.setattr(tool_manifest.shutil, "which", lambda binary: f"/usr/bin/{binary}")

    def fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=2, stdout="", stderr="")

    monkeypatch.setattr(tool_manifest.subprocess, "run", fake_run)

    result = tool_manifest.verify_tool_profile("core")

    assert result["installed"] == result["total"]
    assert result["version_ok"] == 0


def test_verify_handles_timeout(monkeypatch):
    """A timeout should not mark an installed binary as missing."""
    monkeypatch.setattr(tool_manifest.shutil, "which", lambda binary: f"/usr/bin/{binary}")

    def fake_run(*args, **kwargs):
        raise tool_manifest.subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs["timeout"])

    monkeypatch.setattr(tool_manifest.subprocess, "run", fake_run)

    result = tool_manifest.verify_tool_profile("core")

    assert result["installed"] == result["total"]
    assert result["version_ok"] == result["total"]
    assert "timed out" in result["tools"][0]["error"]
