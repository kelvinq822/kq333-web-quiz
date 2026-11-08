# -*- coding: utf-8 -*-
"""Generate demo questions and print them (M1-M3 acceptance aid)."""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.generator import GenerationError, build_question  # noqa: E402


def main(n=20, seed=7):
    rng = random.Random(seed)
    counts = {}
    ok = 0
    for i in range(n):
        try:
            q = build_question(rng)
        except GenerationError as exc:
            print("!! generation failed:", exc)
            continue
        ok += 1
        counts[q.tid] = counts.get(q.tid, 0) + 1
        print("=" * 78)
        print("Q%d  [%s %s d%d]  %s" % (i + 1, q.tid, q.topic, q.difficulty, q.stmt))
        letters = "ABCD"
        for j, ch in enumerate(q.choices):
            mark = "*" if j == q.answer_index else " "
            print("  %s %s %s" % (mark, letters[j], ch))
        print("  answer: %s   nota=%s   codes=%s" % (letters[q.answer_index], q.nota, q.codes))
        if q.nota and q.answer_index == 3:
            print("  reveal: %s" % q.answer_tex)
    print("=" * 78)
    print("generated %d/%d" % (ok, n))
    print("templates used:", dict(sorted(counts.items())))


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    main(n)
