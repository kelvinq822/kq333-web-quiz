# -*- coding: utf-8 -*-
"""Pack the data directory into a timestamped tar.gz."""
import os
import sys
import tarfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config  # noqa: E402


def main():
    src = Config.DATA_DIR
    stamp = time.strftime("%Y%m%d-%H%M")
    out = os.path.join(os.path.dirname(src), "backup-%s.tar.gz" % stamp)
    with tarfile.open(out, "w:gz") as tar:
        tar.add(src, arcname="data")
    size = os.path.getsize(out) / 1024.0
    print("wrote %s (%.1f KB)" % (out, size))


if __name__ == "__main__":
    main()
