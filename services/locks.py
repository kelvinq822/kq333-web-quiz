"""Cross-platform advisory lock built on O_CREAT|O_EXCL lock files."""
from __future__ import annotations

import os
import time


class LockTimeout(RuntimeError):
    pass


class FileLock:
    """Short-lived lock.  Stale locks older than `stale` seconds are broken."""

    def __init__(self, path: str, timeout: float = 3.0, stale: float = 10.0, poll: float = 0.05):
        self.path = path
        self.timeout = timeout
        self.stale = stale
        self.poll = poll
        self.fd = None

    def __enter__(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        deadline = time.time() + self.timeout
        while True:
            try:
                self.fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(self.fd, str(os.getpid()).encode())
                return self
            except FileExistsError:
                try:
                    age = time.time() - os.path.getmtime(self.path)
                    if age > self.stale:
                        os.unlink(self.path)
                        continue
                except OSError:
                    pass
                if time.time() >= deadline:
                    raise LockTimeout(self.path)
                time.sleep(self.poll)

    def __exit__(self, *exc):
        try:
            if self.fd is not None:
                os.close(self.fd)
        finally:
            self.fd = None
            try:
                os.unlink(self.path)
            except OSError:
                pass
        return False
