# ShikariMCP - local artifact storage

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shikari.config import get_config


def write_artifact(run_id: str, name: str, content: str, kind: str = "text") -> dict[str, Any]:
    """Persist command output locally and return an artifact reference."""
    path = artifact_path(run_id, name, kind)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return artifact_reference(path, name, kind)


def artifact_path(run_id: str, name: str, kind: str = "text") -> Path:
    """Allocate a stable path inside Shikari's configured artifact directory."""
    base_dir = Path(get_config().artifact_dir).expanduser().resolve(strict=False)
    suffixes = {
        "json": ".json",
        "jsonl": ".jsonl",
        "xml": ".xml",
        "stderr": ".stderr.txt",
    }
    suffix = suffixes.get(kind, ".txt")
    safe_run_id = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in run_id)
    safe_name = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in name)
    return base_dir / f"{safe_run_id}_{safe_name}{suffix}"


def artifact_reference(path: str | Path, name: str, kind: str = "text") -> dict[str, Any]:
    """Return metadata for an existing artifact."""
    artifact = Path(path)
    return {
        "name": name,
        "kind": kind,
        "path": str(artifact),
        "bytes": artifact.stat().st_size if artifact.exists() else 0,
    }


def write_json_artifact(run_id: str, name: str, payload: Any) -> dict[str, Any]:
    """Persist JSON artifact data."""
    return write_artifact(
        run_id=run_id,
        name=name,
        content=json.dumps(payload, indent=2, sort_keys=True),
        kind="json",
    )


def read_artifact(path: str, offset: int = 0, max_chars: int = 20000) -> dict[str, Any]:
    """Read a bounded artifact segment without allowing paths outside storage."""
    base_dir = Path(get_config().artifact_dir).expanduser().resolve(strict=False)
    artifact = Path(path).expanduser().resolve(strict=False)
    try:
        artifact.relative_to(base_dir)
    except ValueError as exc:
        raise ValueError("Artifact path is outside SHIKARI_ARTIFACT_DIR.") from exc
    if not artifact.is_file():
        raise ValueError(f"Artifact does not exist: {path}")

    safe_offset = max(0, offset)
    safe_limit = min(max(max_chars, 1), get_config().max_output_chars)
    with artifact.open("r", encoding="utf-8", errors="replace") as handle:
        handle.seek(safe_offset)
        content = handle.read(safe_limit)
        next_offset = handle.tell()
        complete = handle.read(1) == ""
    return {
        "path": str(artifact),
        "offset": safe_offset,
        "next_offset": next_offset,
        "complete": complete,
        "content": content,
    }
