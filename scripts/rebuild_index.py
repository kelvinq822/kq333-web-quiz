# -*- coding: utf-8 -*-
"""Rebuild names.json from the user profiles (recovery tool)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config  # noqa: E402
from services.filestore import Store  # noqa: E402
from services.users import rebuild_index  # noqa: E402


def main():
    store = Store(Config.DATA_DIR)
    idx = rebuild_index(store)
    print("indexed %d user(s)" % len(idx))
    for key in sorted(idx):
        print("  %s -> %s" % (key, idx[key]))


if __name__ == "__main__":
    main()
