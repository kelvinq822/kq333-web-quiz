# -*- coding: utf-8 -*-
"""Core maths tests: differentiation, tidy, MCQ invariants."""
import math
import os
import random
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from exprlib import evaluate, to_latex  # noqa: E402
from exprlib.diff import diff  # noqa: E402
from exprlib.tidy import tidy  # noqa: E402

from bank.templates import BUILDERS  # noqa: E402
from services.compare import subst_dydx  # noqa: E402
from services.generator import build_question  # noqa: E402

ALL_TIDS = sorted(BUILDERS)


def _central(fn, x, h=1e-6):
    return (fn(x + h) - fn(x - h)) / (2 * h)


@pytest.mark.parametrize("tid", ALL_TIDS)
def test_explicit_derivative_matches_finite_difference(tid):
    if tid.startswith("IM"):
        pytest.skip("implicit covered separately")
    rng = random.Random(hash(tid) & 0xFFFF)
    checked = 0
    for _ in range(40):
        built = BUILDERS[tid](rng)
        ans = tidy(diff(built.expr))
        for x in built.xs:
            try:
                d0 = evaluate(ans, x)
            except (ValueError, ZeroDivisionError, OverflowError):
                continue
            fd = _central(lambda t: evaluate(built.expr, t), x)
            assert math.isfinite(fd)
            scale = max(1.0, abs(fd))
            assert abs(d0 - fd) / scale < 1e-4, (tid, x, d0, fd)
            checked += 1
    assert checked >= 10


def _solve_y(fun, x, y0, span=0.25, steps=800):
    """Find y near y0 with fun(x, y) == 0 by scanning and bisecting."""
    lo, hi = y0 - span, y0 + span

    def f(y):
        return fun(x, y)

    prev_y, prev_v = lo, f(lo)
    for i in range(1, steps + 1):
        y = lo + (hi - lo) * i / steps
        v = f(y)
        if prev_v == 0:
            return prev_y
        if prev_v * v < 0:
            a, b = prev_y, y
            for _ in range(80):
                m = (a + b) / 2
                if f(a) * f(m) <= 0:
                    b = m
                else:
                    a = m
            return (a + b) / 2
        prev_y, prev_v = y, v
    return None


@pytest.mark.parametrize("tid", ["IM1", "IM2", "IM3", "IM4", "IM5", "IM7"])
def test_implicit_derivative_holds(tid):
    rng = random.Random(hash(tid) & 0xFFFF)
    checked = 0

    for _ in range(20):
        built = BUILDERS[tid](rng)
        dl, dr = tidy(diff(built.lhs)), tidy(diff(built.rhs))

        def f(xx, yy):
            try:
                return evaluate(built.lhs, xx, yy) - evaluate(built.rhs, xx, yy)
            except (ValueError, ZeroDivisionError, OverflowError):
                return float("nan")

        for (x, y) in built.points:
            if not (math.isfinite(x) and math.isfinite(y)):
                continue
            h = 1e-5
            y1 = _solve_y(f, x + h, y)
            y2 = _solve_y(f, x - h, y)
            if y1 is None or y2 is None:
                continue
            if abs(y1 - y) > 0.01 or abs(y2 - y) > 0.01:
                continue  # jumped to another branch
            dydx = (y1 - y2) / (2 * h)
            lh = evaluate(subst_dydx(dl, dydx), x, y)
            rh = evaluate(subst_dydx(dr, dydx), x, y)
            scale = max(1.0, abs(lh), abs(rh))
            assert abs(lh - rh) / scale < 1e-2, (tid, x, y, dydx, lh, rh)
            checked += 1
    assert checked >= 5


def test_tidy_is_idempotent():
    for tid in ALL_TIDS:
        rng = random.Random(9)
        for _ in range(10):
            b = BUILDERS[tid](rng)
            if b.expr is None:
                continue
            once = tidy(diff(b.expr))
            assert tidy(once) == once


def test_mcq_invariants():
    rng = random.Random(4)
    for _ in range(200):
        q = build_question(rng)
        assert len(q.choices) == 4
        assert 0 <= q.answer_index < 4
        assert len(set(q.choices)) == 4
        if q.nota:
            assert q.choices[3] == "以上皆非"
            assert (q.answer_index == 3) == (q.codes[q.answer_index] == "none_of_above")
        else:
            assert q.choices[3] != "以上皆非"


def test_nota_rates():
    rng = random.Random(12)
    n = 400
    nota = 0
    nota_answer = 0
    for _ in range(n):
        q = build_question(rng)
        nota += 1 if q.nota else 0
        nota_answer += 1 if q.nota and q.answer_index == 3 else 0
    assert 0.25 < nota / n < 0.45
    assert 0.08 < nota_answer / n < 0.28


def test_answer_positions_balanced():
    rng = random.Random(21)
    counts = [0, 0, 0, 0]
    for _ in range(400):
        q = build_question(rng)
        counts[q.answer_index] += 1
    for c in counts:
        assert 50 < c < 160, counts

