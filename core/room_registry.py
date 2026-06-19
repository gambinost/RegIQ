"""Active room registry — tracks which rooms were created in this server session.

Agents check this before processing messages to avoid picking up old Band rooms.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

_ACTIVE_ROOMS_FILE = Path(__file__).parent.parent / "data" / "active_rooms.json"
_lock = threading.Lock()


def register_room(room_id: str) -> None:
    """Add a room to the active set (called by trigger endpoint)."""
    with _lock:
        active = _load()
        active.add(room_id)
        _save(active)


def is_active_room(room_id: str) -> bool:
    """Check if a room was created in this server session (called by agents)."""
    with _lock:
        return room_id in _load()


def _load() -> set[str]:
    if _ACTIVE_ROOMS_FILE.exists():
        try:
            return set(json.loads(_ACTIVE_ROOMS_FILE.read_text()))
        except (json.JSONDecodeError, OSError):
            pass
    return set()


def _save(active: set[str]) -> None:
    _ACTIVE_ROOMS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _ACTIVE_ROOMS_FILE.write_text(json.dumps(sorted(active)))
