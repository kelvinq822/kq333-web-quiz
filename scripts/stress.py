# -*- coding: utf-8 -*-
"""Stress the generator: coverage per template, failure rate, timing."""
import collections
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.generator import GenerationError, META, build_question  # noqa: E402


def main(n=300, seed=11):
    rng = random.Random(seed)
    counts = collections.Counter()
    fails = 0
    t0 = time.time()
    nota = 0
    nota_answer = 0
    for _ in range(n):
        try:
            q = build_question(rng)
        except GenerationError:
            fails += 1
            continue
        counts[q.tid] += 1
        nota += 1 if q.nota else 0
        nota_answer += 1 if (q.nota and q.answer_index == 3) else 0
    dt = time.time() - t0
    print("requested %d, generated %d, failed %d" % (n, n - fails, fails))
    print("time total %.2fs, per question %.1f ms" % (dt, dt * 1000 / max(1, n - fails)))
    print("nota rate %.1f%% (target 35%%), nota-answer %.1f%% (target 17.5%%)" % (
        100.0 * nota / max(1, n - fails), 100.0 * nota_answer / max(1, n - fails)))
    missing = [t for t in META if counts[t] == 0]
    print("templates seen %d/%d" % (len(counts), len(META)))
    if missing:
        print("never seen:", sorted(missing))
    for tid in sorted(counts):
        print("  %-4s %3d" % (tid, counts[tid]))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 300)
