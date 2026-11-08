"""Pending questions: the answer never leaves the server (v2.0 section 11.2)."""
from __future__ import annotations

import os
import time

TTL_SECONDS = 60 * 60


def save(store, question, uid: str) -> None:
    payload = {
        "qid": question.qid,
        "uid": uid,
        "tid": question.tid,
        "topic": question.topic,
        "difficulty": question.difficulty,
        "stmt": question.stmt,
        "choices": question.choices,
        "answer_index": question.answer_index,
        "codes": question.codes,
        "nota": question.nota,
        "answer_tex": question.answer_tex,
        "created_at": int(time.time()),
    }
    store.write_json(store.pending_path(question.qid), payload)


def load(store, qid: str):
    if not qid or not all(c in "0123456789abcdef" for c in qid):
        return None
    return store.read_json(store.pending_path(qid))


def consume(store, qid: str) -> bool:
    """Delete the pending file; False when it was already gone (replay)."""
    return store.remove(store.pending_path(qid))


def cleanup(store, ttl: int = TTL_SECONDS) -> int:
    removed = 0
    cutoff = time.time() - ttl
    try:
        entries = os.scandir(store.pending)
    except OSError:
        return 0
    with entries:
        for entry in entries:
            try:
                if entry.is_file() and entry.stat().st_mtime < cutoff:
                    os.unlink(entry.path)
                    removed += 1
            except OSError:
                continue
    return removed
