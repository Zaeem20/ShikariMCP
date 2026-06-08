"""Tests for bounded, confined artifact access."""

import pytest

from shikari.config import ShikariConfig, set_config
from shikari.core.artifacts import artifact_path, read_artifact, write_artifact


def test_artifact_reads_are_bounded(tmp_path):
    set_config(ShikariConfig(artifact_dir=str(tmp_path), max_output_chars=1024))
    artifact = write_artifact("run", "output", "abcdef")

    first = read_artifact(artifact["path"], offset=0, max_chars=3)
    second = read_artifact(artifact["path"], offset=first["next_offset"], max_chars=3)

    assert first["content"] == "abc"
    assert first["complete"] is False
    assert second["content"] == "def"
    assert second["complete"] is True


def test_artifact_path_escape_is_rejected(tmp_path):
    artifact_dir = tmp_path / "artifacts"
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    set_config(ShikariConfig(artifact_dir=str(artifact_dir)))

    with pytest.raises(ValueError, match="outside"):
        read_artifact(str(outside))


def test_artifact_path_sanitizes_run_id(tmp_path):
    set_config(ShikariConfig(artifact_dir=str(tmp_path)))
    path = artifact_path("../../escape", "output")
    assert path.parent == tmp_path.resolve()
    assert ".." not in path.name
