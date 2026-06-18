"""Tests for MCP boundary input validation."""

import pytest
from pydantic import ValidationError

from shikari.core.input_validation import (
    ArtifactReadInputs,
    ListRunsInputs,
    RunQueryInputs,
    ToolExplainInputs,
    ToolListInputs,
    ToolRunInputs,
)


class TestToolRunInputs:
    def test_valid_minimal(self):
        v = ToolRunInputs(tool_id="nmap_scan", inputs={"target": "10.0.0.1"})
        assert v.tool_id == "nmap_scan"
        assert v.template == "safe"
        assert v.dry_run is True

    def test_valid_full(self):
        v = ToolRunInputs(
            tool_id="nuclei_scan",
            inputs={"target": "http://example.com", "severity": "high"},
            profile="web",
            template="safe",
            dry_run=False,
        )
        assert v.profile == "web"
        assert v.dry_run is False

    def test_rejects_empty_tool_id(self):
        with pytest.raises(ValidationError, match="at least 1 character"):
            ToolRunInputs(tool_id="", inputs={})

    def test_rejects_invalid_tool_id_chars(self):
        with pytest.raises(ValidationError, match="Invalid tool_id"):
            ToolRunInputs(tool_id="nmap; rm -rf /", inputs={})

    def test_rejects_tool_id_with_spaces(self):
        with pytest.raises(ValidationError, match="Invalid tool_id"):
            ToolRunInputs(tool_id="nmap scan", inputs={})

    def test_rejects_tool_id_too_long(self):
        with pytest.raises(ValidationError, match="at most 128 characters"):
            ToolRunInputs(tool_id="x" * 129, inputs={})

    def test_rejects_invalid_template(self):
        with pytest.raises(ValidationError, match="Invalid template"):
            ToolRunInputs(tool_id="nmap_scan", inputs={}, template="safe; cat /etc/passwd")

    def test_rejects_too_many_inputs(self):
        inputs = {f"key_{i}": f"val_{i}" for i in range(51)}
        with pytest.raises(ValidationError, match="Too many input parameters"):
            ToolRunInputs(tool_id="nmap_scan", inputs=inputs)

    def test_rejects_huge_input_value(self):
        with pytest.raises(ValidationError, match="exceeds 1MB"):
            ToolRunInputs(tool_id="nmap_scan", inputs={"target": "x" * 2_000_000})

    def test_validates_profile_none(self):
        v = ToolRunInputs(tool_id="nmap_scan", inputs={}, profile=None)
        assert v.profile is None


class TestArtifactReadInputs:
    def test_valid(self):
        v = ArtifactReadInputs(path=".shikari/artifacts/abc_nmap_stdout.xml")
        assert v.offset == 0
        assert v.max_chars == 20000

    def test_rejects_path_traversal(self):
        with pytest.raises(ValidationError, match="Path traversal"):
            ArtifactReadInputs(path="../../etc/passwd")

    def test_rejects_null_bytes(self):
        with pytest.raises(ValidationError, match="null bytes"):
            ArtifactReadInputs(path="test\x00.txt")

    def test_rejects_empty_path(self):
        with pytest.raises(ValidationError, match="at least 1 character"):
            ArtifactReadInputs(path="")

    def test_offset_bounds(self):
        with pytest.raises(ValidationError):
            ArtifactReadInputs(path="test.txt", offset=-1)

    def test_max_chars_bounds(self):
        with pytest.raises(ValidationError):
            ArtifactReadInputs(path="test.txt", max_chars=0)
        with pytest.raises(ValidationError):
            ArtifactReadInputs(path="test.txt", max_chars=300_000)


class TestToolExplainInputs:
    def test_valid(self):
        v = ToolExplainInputs(tool_id="nmap_scan", profile="core")
        assert v.tool_id == "nmap_scan"

    def test_rejects_bad_tool_id(self):
        with pytest.raises(ValidationError):
            ToolExplainInputs(tool_id="nmap scan")


class TestRunQueryInputs:
    def test_valid_uuid(self):
        v = RunQueryInputs(run_id="550e8400-e29b-41d4-a716-446655440000")
        assert v.run_id == "550e8400-e29b-41d4-a716-446655440000"

    def test_rejects_non_uuid(self):
        with pytest.raises(ValidationError, match="Invalid run_id format"):
            RunQueryInputs(run_id="not-a-uuid")


class TestListRunsInputs:
    def test_valid(self):
        v = ListRunsInputs(limit=50)
        assert v.limit == 50

    def test_rejects_zero(self):
        with pytest.raises(ValidationError):
            ListRunsInputs(limit=0)

    def test_rejects_over_100(self):
        with pytest.raises(ValidationError):
            ListRunsInputs(limit=101)


class TestToolListInputs:
    def test_valid_profile(self):
        v = ToolListInputs(profile="core")
        assert v.profile == "core"

    def test_valid_none(self):
        v = ToolListInputs(profile=None)
        assert v.profile is None

    def test_rejects_unknown_profile(self):
        with pytest.raises(ValidationError, match="Unknown profile"):
            ToolListInputs(profile="nonexistent_profile_xyz")
