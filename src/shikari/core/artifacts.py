# ShikariMCP - local artifact storage

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shikari.config import get_config


def write_artifact(run_id: str, name: str, content: str, kind: str = "text") -> dict[str, Any]:
    """Persist command output locally and return an artifact reference."""
    base_dir = Path(get_config().audit_log_path).parent / "artifacts"
    base_dir.mkdir(parents=True, exist_ok=True)

    suffix = ".json" if kind == "json" else ".txt"
    safe_name = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in name)
    path = base_dir / f"{run_id}_{safe_name}{suffix}"
    path.write_text(content, encoding="utf-8")
    return {
        "name": name,
        "kind": kind,
        "path": str(path),
        "bytes": len(content.encode("utf-8")),
    }


def write_json_artifact(run_id: str, name: str, payload: Any) -> dict[str, Any]:
    """Persist JSON artifact data."""
    return write_artifact(
        run_id=run_id,
        name=name,
        content=json.dumps(payload, indent=2, sort_keys=True),
        kind="json",
    )
