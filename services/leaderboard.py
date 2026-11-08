"""All-time leaderboard computed from profile files, cached for 30s."""
from __future__ import annotations

import os
import time

CACHE_SECONDS = 30
_cache = {"at": 0.0, "rows": None}


def _scan(store):
    rows = []
    try:
        entries = list(os.scandir(store.users))
    except OSError:
        return rows
    for entry in entries:
        if not entry.is_dir():
            continue
        profile = store.read_json(os.path.join(entry.path, "profile.json"))
        if not profile:
            continue
        attempts = profile.get("attempts", 0)
        correct = profile.get("correct", 0)
        rows.append(
            {
                "uid": profile.get("uid", entry.name),
                "name": profile.get("username", "?"),
                "points": int(profile.get("points", 0)),
                "correct": int(correct),
                "attempts": int(attempts),
                "accuracy": round(100.0 * correct / attempts, 1) if attempts else 0.0,
                "created_at": profile.get("created_at", ""),
            }
        )
    rows.sort(key=lambda r: (-r["points"], -r["accuracy"], r["created_at"]))
    for i, row in enumerate(rows, 1):
        row["rank"] = i
    return rows


def all_rows(store, force: bool = False):
    now = time.time()
    if force or _cache["rows"] is None or now - _cache["at"] > CACHE_SECONDS:
        _cache["rows"] = _scan(store)
        _cache["at"] = now
    return _cache["rows"]


def rank_of(store, uid: str):
    for row in all_rows(store):
        if row["uid"] == uid:
            return row["rank"], row
    return None, None


def invalidate():
    _cache["at"] = 0.0
    _cache["rows"] = None
