"""Numeric comparison helpers shared by the generator and the MCQ engine."""
from __future__ import annotations

import math

from exprlib.nodes import Add, Cbrt, Div, DYDX, Eq, Func, Mul, Num, Pow, Sqrt, Sym, add, evaluate

MAX_ABS = 1e9


def subst_dydx(n, d):
    """Return a copy of n with the dy/dx symbol replaced by the number d."""
    if isinstance(n, Sym):
        if n.name == "dy/dx":
            return Num(d)
        return n
    if isinstance(n, Num):
        return n
    if isinstance(n, Add):
        return Add(tuple(subst_dydx(t, d) for t in n.terms))
    if isinstance(n, Mul):
        return Mul(tuple(subst_dydx(f, d) for f in n.factors))
    if isinstance(n, Div):
        return Div(subst_dydx(n.num, d), subst_dydx(n.den, d))
    if isinstance(n, Pow):
        return Pow(subst_dydx(n.base, d), n.exp)
    if isinstance(n, Sqrt):
        return Sqrt(subst_dydx(n.arg, d))
    if isinstance(n, Cbrt):
        return Cbrt(subst_dydx(n.arg, d))
    if isinstance(n, Func):
        return Func(n.name, subst_dydx(n.arg, d))
    return n


def eq_node(eq: Eq):
    """Equation as a single expression (lhs - rhs), for numeric comparison."""
    from exprlib.mutate import _neg

    return add(eq.lhs, _neg(eq.rhs))


def safe_eval(node, x=None, y=None):
    try:
        v = evaluate(node, x, y)
    except (ValueError, ZeroDivisionError, OverflowError, TypeError):
        return None
    if not math.isfinite(v) or abs(v) > MAX_ABS:
        return None
    return v


def values_at(node, points, has_dydx=False, dvals=(0.7, -1.3)):
    """Numeric fingerprints of node on the sample points (None if invalid)."""
    out = []
    for (x, y) in points:
        if has_dydx:
            for d in dvals:
                v = safe_eval(subst_dydx(node, d), x, y)
                if v is None:
                    return None
                out.append(v)
        else:
            v = safe_eval(node, x, y)
            if v is None:
                return None
            out.append(v)
    return out


def differs(a, b, points, has_dydx=False, tol=1e-6, need=4):
    """True when two expressions take clearly different values on the points."""
    va = values_at(a, points, has_dydx)
    vb = values_at(b, points, has_dydx)
    if va is None or vb is None:
        return False
    usable = 0
    for u, v in zip(va, vb):
        scale = max(1.0, abs(u), abs(v))
        if abs(u - v) / scale > tol:
            usable += 1
    return usable >= need
