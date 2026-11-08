"""Player accounts stored as directories under data/users/<uid>/."""
from __future__ import annotations

import datetime
import hashlib
import os
import re
import unicodedata

MAX_USERS = 50
NAME_RE = re.compile(r"^[0-9A-Za-z_\u4e00-\u9fff]{3,16}$")


class NameError_(ValueError):
    pass


def normalize_name(name: str) -> str:
    if not isinstance(name, str):
        raise NameError_("請輸入用戶名")
    name = unicodedata.normalize("NFKC", name).strip()
    if not NAME_RE.match(name):
        raise NameError_("用戶名需為 3–16 個中英文字、數字或底線")
    return name


def name_key(name: str) -> str:
    """Case-insensitive key for ASCII, exact for CJK."""
    return name.lower() if name.isascii() else name


def uid_for(name: str) -> str:
    return hashlib.sha1(name_key(name).encode("utf-8")).hexdigest()[:16]


def _now_iso() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def _today() -> str:
    return datetime.datetime.now().astimezone().date().isoformat()


def _read_index(store):
    idx = store.read_json(store.names, default=None)
    return idx if isinstance(idx, dict) else {}


def load_index(store):
    idx = _read_index(store)
    if idx:
        return idx
    return rebuild_index(store)


def rebuild_index(store):
    idx = {}
    users_dir = store.users
    if os.path.isdir(users_dir):
        for uid in os.listdir(users_dir):
            profile = store.read_json(store.profile_path(uid))
            if profile and profile.get("username"):
                idx[name_key(profile["username"])] = uid
    with store.system_lock():
        store.write_json(store.names, idx)
    return idx


def get_profile(store, uid):
    return store.read_json(store.profile_path(uid))


def login_or_register(store, raw_name):
    name = normalize_name(raw_name)
    key = name_key(name)
    load_index(store)  # make sure names.json exists before taking the lock
    with store.system_lock():
        idx = _read_index(store)
        uid = idx.get(key)
        if uid:
            profile = store.read_json(store.profile_path(uid))
            if profile:
                return profile
        if len(idx) >= MAX_USERS:
            raise NameError_("人數已滿（上限 %d 人）" % MAX_USERS)
        uid = uid_for(name)
        while os.path.exists(store.profile_path(uid)):
            uid = hashlib.sha1((key + uid).encode("utf-8")).hexdigest()[:16]
        profile = {
            "v": 1,
            "username": name,
            "uid": uid,
            "created_at": _now_iso(),
            "last_seen_at": _now_iso(),
            "points": 0,
            "correct": 0,
            "attempts": 0,
            "streak": 0,
            "day": _today(),
            "day_correct": 0,
            "day_attempts": 0,
        }
        store.write_json(store.profile_path(uid), profile)
        idx[key] = uid
        store.write_json(store.names, idx)
        return profile


def record_answer(store, uid, q, choice, ms, award=True):
    """Apply one answer.  Returns (correct, points, profile, wrong_entry|None)."""
    correct = int(choice) == int(q["answer_index"])
    points = int(q["difficulty"]) if (correct and award) else 0
    today = _today()

    with store.user_lock(uid):
        profile = store.read_json(store.profile_path(uid))
        if not profile:
            raise NameError_("找不到帳號")
        if profile.get("day") != today:
            profile["day"] = today
            profile["day_correct"] = 0
            profile["day_attempts"] = 0
        profile["attempts"] += 1
        profile["day_attempts"] += 1
        if correct:
            profile["correct"] += 1
            profile["day_correct"] += 1
            profile["streak"] += 1
            profile["points"] += points
        else:
            profile["streak"] = 0
        profile["last_seen_at"] = _now_iso()
        store.write_json(store.profile_path(uid), profile)

        store.append_line(
            store.attempts_path(uid),
            {
                "t": _now_iso(),
                "qid": q["qid"],
                "tid": q["tid"],
                "topic": q["topic"],
                "diff": q["difficulty"],
                "c": int(choice),
                "ok": 1 if correct else 0,
                "pts": points,
                "ms": int(ms),
                "nota": bool(q.get("nota")),
            },
        )

        entry = None
        if not correct:
            entry = {
                "qid": q["qid"],
                "t": _now_iso(),
                "tid": q["tid"],
                "stmt_tex": q["stmt"],
                "choices": q["choices"],
                "correct_index": q["answer_index"],
                "your_index": int(choice),
                "nota": bool(q.get("nota")),
                "reveal_tex": q.get("answer_tex") if q.get("nota") and q["answer_index"] == 3 else None,
            }
            book = store.read_json(store.wrongbook_path(uid), default=[])
            if not isinstance(book, list):
                book = []
            book.insert(0, entry)
            store.write_json(store.wrongbook_path(uid), book[:200])

    return correct, points, profile, entry


def delete_wrong(store, uid, qid) -> bool:
    with store.user_lock(uid):
        book = store.read_json(store.wrongbook_path(uid), default=[])
        if not isinstance(book, list):
            return False
        kept = [e for e in book if e.get("qid") != qid]
        if len(kept) == len(book):
            return False
        store.write_json(store.wrongbook_path(uid), kept)
        return True
