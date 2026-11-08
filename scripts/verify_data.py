# -*- coding: utf-8 -*-
"""Check that profiles, attempts and the leaderboard agree."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config  # noqa: E402
from services.filestore import Store  # noqa: E402
from services.users import rebuild_index  # noqa: E402


def main():
    store = Store(Config.DATA_DIR)
    problems = 0
    users = 0
    for uid in sorted(os.listdir(store.users)):
        path = store.profile_path(uid)
        if not os.path.exists(path):
            print("!! %s: missing profile.json" % uid)
            problems += 1
            continue
        profile = store.read_json(path)
        if not profile:
            print("!! %s: unreadable profile.json" % uid)
            problems += 1
            continue
        users += 1
        attempts = store.tail_lines(store.attempts_path(uid), 10 ** 9)
        total_pts = sum(a.get("pts", 0) for a in attempts)
        correct = sum(1 for a in attempts if a.get("ok"))
        if total_pts != profile.get("points", 0):
            print("!! %s: points %s != attempts %s" % (uid, profile.get("points"), total_pts))
            problems += 1
        if correct != profile.get("correct", 0):
            print("!! %s: correct %s != attempts %s" % (uid, profile.get("correct"), correct))
            problems += 1
        if len(attempts) != profile.get("attempts", 0):
            print("!! %s: attempts %s != log %s" % (uid, profile.get("attempts"), len(attempts)))
            problems += 1
        book = store.read_json(store.wrongbook_path(uid), default=[])
        if not isinstance(book, list):
            print("!! %s: wrongbook is not a list" % uid)
            problems += 1

    names = store.read_json(store.names, default={}) or {}
    for key, uid in names.items():
        if not os.path.exists(store.profile_path(uid)):
            print("!! names.json points at missing user %r" % uid)
            problems += 1

    orphans = 0
    for entry in os.scandir(store.pending):
        if entry.is_file() and _older_than(entry, 3600):
            orphans += 1

    print("users checked: %d" % users)
    print("stale pending files (>1h): %d" % orphans)
    print("problems: %d" % problems)
    if problems:
        print("rebuilding names.json ...")
        rebuild_index(store)
    return 1 if problems else 0


def _older_than(entry, seconds):
    import time

    try:
        return time.time() - entry.stat().st_mtime > seconds
    except OSError:
        return False


if __name__ == "__main__":
    raise SystemExit(main())
