# -*- coding: utf-8 -*-
"""Create the data directory layout (safe to run repeatedly)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config  # noqa: E402
from services.filestore import Store  # noqa: E402


def main():
    store = Store(Config.DATA_DIR)
    if not os.path.exists(store.names):
        store.write_json(store.names, {})
    print("data dir:", store.root)
    print("users   :", store.users)
    print("pending :", store.pending)


if __name__ == "__main__":
    main()
