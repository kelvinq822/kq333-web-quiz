"""Very small in-memory rate limiter (single worker on PythonAnywhere)."""
from __future__ import annotations

import time
from collections import defaultdict, deque

_hits = defaultdict(deque)


def allow(key: str, limit: int, window: float) -> bool:
    now = time.time()
    bucket = _hits[key]
    while bucket and now - bucket[0] > window:
        bucket.popleft()
    if len(bucket) >= limit:
        return False
    bucket.append(now)
    return True


def reset():
    _hits.clear()
