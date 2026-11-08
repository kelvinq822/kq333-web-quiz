"""Filesystem storage: atomic JSON writes, append-only JSONL, path helpers."""
from __future__ import annotations

import json
import os
import shutil

from .locks import FileLock


class Store:
    def __init__(self, root: str):
        self.root = os.path.abspath(root)
        self.users = os.path.join(self.root, "users")
        self.pending = os.path.join(self.root, "pending")
        self.locks = os.path.join(self.root, "locks")
        self.names = os.path.join(self.root, "names.json")
        for d in (self.users, self.pending, self.locks):
            os.makedirs(d, exist_ok=True)

    # ------------------------------------------------------------- paths
    def user_dir(self, uid: str) -> str:
        return os.path.join(self.users, uid)

    def profile_path(self, uid: str) -> str:
        return os.path.join(self.user_dir(uid), "profile.json")

    def attempts_path(self, uid: str) -> str:
        return os.path.join(self.user_dir(uid), "attempts.jsonl")

    def wrongbook_path(self, uid: str) -> str:
        return os.path.join(self.user_dir(uid), "wrongbook.json")

    def pending_path(self, qid: str) -> str:
        return os.path.join(self.pending, qid + ".json")

    def lock_path(self, name: str) -> str:
        return os.path.join(self.locks, name + ".lock")

    def user_lock(self, uid: str):
        return FileLock(self.lock_path(uid))

    def system_lock(self):
        return FileLock(self.lock_path("system"))

    # -------------------------------------------------------------- read
    def read_json(self, path: str, default=None):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError):
            try:
                with open(path + ".bak", "r", encoding="utf-8") as fh:
                    return json.load(fh)
            except (OSError, ValueError):
                return default

    # ------------------------------------------------------------- write
    def write_json(self, path: str, obj) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = "%s.tmp.%d" % (path, os.getpid())
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, ensure_ascii=False, indent=1)
            fh.flush()
            os.fsync(fh.fileno())
        if os.path.exists(path):
            try:
                shutil.copyfile(path, path + ".bak")
            except OSError:
                pass
        os.replace(tmp, path)

    def append_line(self, path: str, obj) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        line = json.dumps(obj, ensure_ascii=False) + "\n"
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(line)
            fh.flush()
            os.fsync(fh.fileno())

    def tail_lines(self, path: str, n: int = 200):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                lines = fh.readlines()
        except OSError:
            return []
        out = []
        for line in lines[-n:]:
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
        return out

    def remove(self, path: str) -> bool:
        try:
            os.unlink(path)
            return True
        except OSError:
            return False
