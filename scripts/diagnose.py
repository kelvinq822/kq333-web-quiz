# -*- coding: utf-8 -*-
"""Diagnose why one template fails to produce questions."""
import os
import random
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from exprlib.diff import diff
from exprlib.latex import to_latex
from exprlib.nodes import Eq
from exprlib.tidy import tidy

from bank.templates import BUILDERS
from services.compare import eq_node
from services.generator import MAX_ANSWER_LEN, _valid_explicit_points, _valid_implicit_points
from services.mcq import build_options


def diag(tid, n=30):
    rng = random.Random(3)
    reasons = Counter()
    for _ in range(n):
        built = BUILDERS[tid](rng)
        implicit = built.lhs is not None
        if implicit:
            ans = Eq(tidy(diff(built.lhs)), tidy(diff(built.rhs)))
            pts = _valid_implicit_points(built.lhs, built.rhs, ans.lhs, ans.rhs, built.points)
            key = eq_node(ans)
        else:
            ans = tidy(diff(built.expr))
            pts = _valid_explicit_points(built.expr, ans, built.xs)
            key = ans
        if len(pts) < 4:
            reasons["points=%d" % len(pts)] += 1
            continue
        text = to_latex(key)
        if len(text) > MAX_ANSWER_LEN:
            reasons["len=%d" % len(text)] += 1
            continue
        opts = build_options(ans, pts, implicit, rng)
        if opts is None:
            reasons["options"] += 1
            continue
        reasons["ok"] += 1
    print(tid, dict(reasons))


if __name__ == "__main__":
    for tid in sys.argv[1:] or ["QT1"]:
        diag(tid)
