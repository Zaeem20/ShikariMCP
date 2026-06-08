# ShikariMCP - append-only audit events

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from shikari.config import get_config

logger = logging.getLogger("shikari.audit")
_audit_lock = threading.Lock()


def audit_event(event_type: str, **fields: Any) -> None:
    """Write a compact JSONL audit event when auditing is enabled."""
    config = get_config()
    if not config.audit_enabled:
        return

    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event_type,
        **fields,
    }

    try:
        with _audit_lock:
            path = Path(config.audit_log_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, sort_keys=True) + "\n")
    except Exception as exc:
        logger.warning("Failed to write audit event: %s", exc)
