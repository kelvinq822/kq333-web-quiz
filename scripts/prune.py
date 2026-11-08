# -*- coding: utf-8 -*-
"""Housekeeping: drop stale pending questions, trim huge attempt logs."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config  # noqa: E402
from services.filestore import Store  # noqa: E402
import services.pending as pending  # noqa: E402

KEEP_ATTEMPTS = 5000


def main():
    store = Store(Config.DATA_DIR)
    removed = pending.cleanup(store)
    print("removed %d stale pending file(s)" % removed)

    for uid in os.listdir(store.users):
        path = store.attempts_path(uid)
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
        if len(lines) <= KEEP_ATTEMPTS:
            continue
        keep = lines[-KEEP_ATTEMPTS:]
        archive = path + ".archive"
        with open(archive, "a", encoding="utf-8") as fh:
            fh.writelines(lines[:-KEEP_ATTEMPTS])
        with open(path, "w", encoding="utf-8") as fh:
            fh.writelines(keep)
        print("%s: archived %d line(s)" % (uid, len(lines) - KEEP_ATTEMPTS))


if __name__ == "__main__":
    main()
