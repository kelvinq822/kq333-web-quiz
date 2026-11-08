"""The 25 question templates (v2.0 section 2 / appendix A).

Each builder returns a Built record.  Statements are written by hand so the
question keeps the notation of the original worksheets; the answer side is
always produced mechanically by exprlib (and therefore always uses fractional
exponents, per the v1.3 decision).
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from fractions import Fraction

from exprlib import (
    Add, Cbrt, Div, Func, Mul, Node, Num, Pow, Sqrt, Sym, X, Y,
    add, cbrt, div, fn, mul, num, power, sqrt, to_latex,
)

R = random.Random


@dataclass
class Built:
    tid: str
    topic: str
    difficulty: int
    stmt: str
    expr: Node | None = None
    lhs: Node | None = None
    rhs: Node | None = None
    xs: list = field(default_factory=list)
    points: list = field(default_factory=list)


def _p(n: Node) -> str:
    """Parenthesised latex for a factor in the question statement."""
    s = to_latex(n)
    if isinstance(n, (Add, Mul, Div)):
        return r"\left(%s\right)" % s
    return s


def _sign_coef(c: int) -> str:
    return ("+ %d" % c) if c >= 0 else ("- %d" % abs(c))


def _xs(rng, n=8, lo=0.4, hi=2.4, allow_negative=False):
    vals = []
    pool = [0.5, 0.65, 0.8, 1.1, 1.3, 1.6, 1.9, 2.2, 2.6]
    rng.shuffle(pool)
    vals.extend(pool[:n])
    if allow_negative:
        vals.extend([-0.6, -0.9, -1.4, -2.1])
    return vals


# ------------------------------------------------------------------ power

def pw1(rng: R) -> Built:
    a = rng.choice([2, 3, 4, 5])
    m, n = rng.choice([(1, 2), (3, 2), (5, 2)])
    b = rng.choice([2, 3, 4])
    p = rng.choice([1, 2])
    c = rng.choice([1, 2, 3])
    k = rng.choice([2, 3])
    d = rng.choice([1, 2, 3])
    e = Fraction(m, n)
    expr = add(
        mul(num(a), power(X, e)),
        mul(num(-b), power(X, -p)),
        mul(num(c), power(X, k)),
        num(d),
    )
    return Built("PW1", "power", 1, "y = " + to_latex(expr), expr=expr, xs=_xs(rng))


def pw2(rng: R) -> Built:
    c = rng.choice([2, 3, 4, 5])
    m, n = rng.choice([(3, 2), (5, 3), (4, 3)])
    expr = mul(num(c), power(X, -Fraction(m, n)))
    stmt = r"y = \dfrac{%d}{x^{%d/%d}}" % (c, m, n)
    return Built("PW2", "power", 1, stmt, expr=expr, xs=_xs(rng))


def pw5(rng: R) -> Built:
    a = rng.choice([1, 2, 3])
    c = rng.choice([1, 2, 3, 4])
    root = rng.choice([2, 3])
    poly = add(mul(num(a), power(X, 3)), num(c))
    expr = power(poly, Fraction(-1, root))
    if root == 2:
        stmt = r"y = \dfrac{1}{\sqrt{%s}}" % to_latex(poly)
    else:
        stmt = r"y = \dfrac{1}{\sqrt[3]{%s}}" % to_latex(poly)
    return Built("PW5", "power", 2, stmt, expr=expr, xs=_xs(rng))


def pw6(rng: R) -> Built:
    a = rng.choice([1, 2, 3])
    b = rng.choice([2, 3])
    c = rng.choice([1, 2])
    inner = add(mul(num(a), X), power(add(mul(num(b), X), num(c)), 3))
    expr = power(inner, Fraction(1, 3))
    stmt = r"y = \sqrt[3]{%s}" % to_latex(inner)
    return Built("PW6", "power", 3, stmt, expr=expr, xs=_xs(rng))


# ---------------------------------------------------------------- product

def pd1(rng: R) -> Built:
    a = rng.choice([2, 3, 4])
    b = rng.choice([1, 2, 3])
    c = rng.choice([2, 3])
    d = rng.choice([2, 3, 4, 5])
    left = add(num(a), mul(num(b), power(X, -2)))
    right = add(mul(num(c), X), mul(num(-d), power(X, -1)))
    expr = mul(left, right)
    stmt = r"y = \left(%d + \dfrac{%d}{x^{2}}\right)\left(%dx - \dfrac{%d}{x}\right)" % (
        a, b, c, d,
    )
    return Built("PD1", "product", 2, stmt, expr=expr, xs=_xs(rng))


def pd2(rng: R) -> Built:
    b = rng.choice([1, 2, 3])
    d = rng.choice([1, 2, 3])
    m = rng.choice([3, 4])
    n = rng.choice([3, 4])
    a = rng.choice([2, 3])
    c = rng.choice([2, 3])
    expr = mul(power(add(mul(num(a), X), num(b)), m), power(add(mul(num(c), X), num(-d)), n))
    stmt = r"y = %s^{%d}%s^{%d}" % (
        _p(add(mul(num(a), X), num(b))), m,
        _p(add(mul(num(c), X), num(-d))), n,
    )
    return Built("PD2", "product", 2, stmt, expr=expr, xs=_xs(rng))


def pd3(rng: R) -> Built:
    a = rng.choice([2, 3])
    b = rng.choice([1, 2])
    c = rng.choice([1, 2, 3])
    d = rng.choice([2, 3, 4])
    expr = mul(add(mul(num(a), X), num(b)), power(add(mul(num(c), power(X, 2)), num(d)), Fraction(1, 2)))
    stmt = r"y = %s\sqrt{%s}" % (
        _p(add(mul(num(a), X), num(b))),
        to_latex(add(mul(num(c), power(X, 2)), num(d))),
    )
    return Built("PD3", "product", 2, stmt, expr=expr, xs=_xs(rng))


def pd4(rng: R) -> Built:
    n = rng.choice([2, 3])
    k = rng.choice([1, 2, 3])
    expr = mul(power(X, n), Func("tan", mul(num(k), X)))
    stmt = r"y = x^{%d}\tan %s" % (n, _arg_tex(mul(num(k), X)))
    return Built("PD4", "product", 2, stmt, expr=expr, xs=_xs(rng))


def pd5(rng: R) -> Built:
    n = rng.choice([2, 3])
    expr = mul(power(X, n), Func("cos", power(X, Fraction(1, 2))))
    stmt = r"y = x^{%d}\cos\left(\sqrt{x}\right)" % n
    return Built("PD5", "product", 3, stmt, expr=expr, xs=_xs(rng))


def _arg_tex(n: Node) -> str:
    if isinstance(n, Sym):
        return n.name
    return to_latex(n)


# --------------------------------------------------------------- quotient

def qt1(rng: R) -> Built:
    a = rng.choice([2, 3])
    b = rng.choice([1, 2])
    c = rng.choice([2, 3])
    d = rng.choice([1, 2])
    n = rng.choice([2, 3, 4])
    num_node = add(mul(num(a), X), num(b))
    den_node = add(mul(num(c), X), num(d))
    expr = power(div(num_node, den_node), n)
    stmt = r"y = \left(\dfrac{%s}{%s}\right)^{%d}" % (to_latex(num_node), to_latex(den_node), n)
    return Built("QT1", "quotient", 2, stmt, expr=expr, xs=_xs(rng))


def qt3(rng: R) -> Built:
    expr = div(Func("sin", X), add(num(1), Func("cos", X)))
    return Built("QT3", "quotient", 2, r"y = \dfrac{\sin x}{1 + \cos x}", expr=expr, xs=_xs(rng))


def qt4(rng: R) -> Built:
    a = rng.choice([2, 3])
    b = rng.choice([1, 2, 3])
    expr = div(Func("csc", X), add(mul(num(a), X), num(b)))
    stmt = r"y = \dfrac{\csc x}{%dx + %d}" % (a, b)
    return Built("QT4", "quotient", 2, stmt, expr=expr, xs=_xs(rng))


# ------------------------------------------------------------------- trig

def tr1(rng: R) -> Built:
    a = rng.choice([2, 3, 4])
    expr = add(mul(num(a), Func("cot", X)), power(Func("csc", X), 2))
    stmt = r"y = %d\cot x + \csc^{2} x" % a
    return Built("TR1", "trig", 1, stmt, expr=expr, xs=_xs(rng))


def tr2(rng: R) -> Built:
    k = rng.choice([1, 2, 3])
    l = rng.choice([1, 2])
    m = rng.choice([2, 3])
    expr = add(Func("tan", mul(num(k), X)), power(Func("cos", mul(num(l), X)), m))
    stmt = r"y = \tan %s + \cos^{%d} %s" % (_arg_tex(mul(num(k), X)), m, _arg_tex(mul(num(l), X)))
    return Built("TR2", "trig", 2, stmt, expr=expr, xs=_xs(rng))


def tr3(rng: R) -> Built:
    expr = add(
        Func("tan", X),
        mul(num(Fraction(2, 3)), power(Func("tan", X), 3)),
        mul(num(Fraction(1, 5)), power(Func("tan", X), 5)),
    )
    return Built(
        "TR3", "trig", 2,
        r"y = \tan x + \dfrac{2}{3}\tan^{3} x + \dfrac{1}{5}\tan^{5} x",
        expr=expr, xs=_xs(rng),
    )


def tr4(rng: R) -> Built:
    k = rng.choice([1, 2])
    expr = mul(Func("csc", mul(num(k), X)), Func("cot", mul(num(k), X)))
    stmt = r"y = \csc %s\cot %s" % (_arg_tex(mul(num(k), X)), _arg_tex(mul(num(k), X)))
    return Built("TR4", "trig", 2, stmt, expr=expr, xs=_xs(rng))


def tr5(rng: R) -> Built:
    k = rng.choice([1, 2])
    expr = Func("sin", Func("cos", mul(num(k), X)))
    stmt = r"y = \sin\left(\cos %s\right)" % _arg_tex(mul(num(k), X))
    return Built("TR5", "trig", 2, stmt, expr=expr, xs=_xs(rng))


def tr6(rng: R) -> Built:
    expr = power(Func("sec", power(X, Fraction(1, 2))), Fraction(1, 2))
    stmt = r"y = \sqrt{\sec\left(\sqrt{x}\right)}"
    return Built("TR6", "trig", 3, stmt, expr=expr, xs=_xs(rng))


# --------------------------------------------------------------- implicit

def _imp_points_y(rng, ys):
    return [(None, y) for y in ys]


def im1(rng: R) -> Built:
    a = rng.choice([2, 3])
    b = rng.choice([2, 3])
    lhs = X
    rhs = power(mul(add(num(a), mul(num(-1), Y)), add(num(b), Y)), Fraction(1, 2))
    stmt = r"x = \sqrt{(%d - y)(%d + y)}" % (a, b)
    ys = [-b + 0.4, -b + 1.0, -b + 1.6, 0.3, 0.8] if b < 2 else [-1.6, -1.0, -0.4, 0.3, 0.8]
    pts = []
    for y in ys:
        v = (a - y) * (b + y)
        if v > 0:
            pts.append((math.sqrt(v), y))
    return Built("IM1", "implicit", 2, stmt, lhs=lhs, rhs=rhs, points=pts)


def im2(rng: R) -> Built:
    lhs = Func("sin", Func("cos", Y))
    rhs = Func("tan", mul(num(Fraction(1, 2)), X))
    stmt = r"\sin(\cos y) = \tan\dfrac{x}{2}"
    pts = []
    for y in [-1.2, -0.6, 0.2, 0.9, 1.5]:
        x = 2 * math.atan(math.sin(math.cos(y)))
        pts.append((x, y))
    return Built("IM2", "implicit", 3, stmt, lhs=lhs, rhs=rhs, points=pts)


def im3(rng: R) -> Built:
    base = rng.choice([2, 3])
    inner = add(num(base), power(add(mul(num(2), Y), num(1)), Fraction(1, 2)))
    lhs = X
    rhs = power(inner, 4)
    stmt = r"x = \left(%d + \sqrt{2y + 1}\right)^{4}" % base
    pts = []
    for y in [-0.2, 0.2, 0.8, 1.6]:
        pts.append(((base + math.sqrt(2 * y + 1)) ** 4, y))
    return Built("IM3", "implicit", 3, stmt, lhs=lhs, rhs=rhs, points=pts)


def im4(rng: R) -> Built:
    lhs = Func("csc", add(power(X, 2), Y))
    rhs = add(Func("sec", X), num(1))
    stmt = r"\csc(x^{2} + y) = \sec x + 1"
    pts = []
    for x in [-0.8, -0.4, 0.3, 0.7, 1.1]:
        c = math.cos(x)
        if c <= 0:
            continue
        ratio = c / (1 + c)
        y = math.asin(ratio) - x * x
        pts.append((x, y))
    return Built("IM4", "implicit", 3, stmt, lhs=lhs, rhs=rhs, points=pts)


def im5(rng: R) -> Built:
    lhs = X
    rhs = power(add(num(3), power(Y, Fraction(1, 2))), Fraction(1, 4))
    stmt = r"x = \sqrt[4]{3 + \sqrt{y}}"
    pts = []
    for y in [0.3, 0.8, 1.5, 2.4]:
        pts.append(((3 + math.sqrt(y)) ** 0.25, y))
    return Built("IM5", "implicit", 3, stmt, lhs=lhs, rhs=rhs, points=pts)


def im6(rng: R) -> Built:
    c = 2023
    lhs = add(mul(Y, Func("sin", X)), mul(X, Func("cos", Y)))
    rhs = num(c)
    stmt = r"y\sin x + x\cos y = 2023"

    def f(y, x):
        return y * math.sin(x) + x * math.cos(y) - c

    solved = []
    for x in (0.7, 0.9, 1.1):
        lo, hi = 0.0, 6000.0
        if f(lo, x) * f(hi, x) > 0:
            continue
        for _ in range(90):
            mid = (lo + hi) / 2
            if f(lo, x) * f(mid, x) <= 0:
                hi = mid
            else:
                lo = mid
        solved.append((x, (lo + hi) / 2))
    return Built("IM6", "implicit", 3, stmt, lhs=lhs, rhs=rhs, points=solved)


def im7(rng: R) -> Built:
    lhs = add(X, Func("cot", Y))
    rhs = mul(X, power(Y, 2))
    stmt = r"x + \cot y = xy^{2}"
    pts = []
    for y in [-2.1, -1.4, 0.4, 0.7, 1.6]:
        if abs(y * y - 1) < 0.2:
            continue
        x = (1.0 / math.tan(y)) / (y * y - 1)
        pts.append((x, y))
    return Built("IM7", "implicit", 3, stmt, lhs=lhs, rhs=rhs, points=pts)


BUILDERS = {
    "PW1": pw1, "PW2": pw2, "PW5": pw5, "PW6": pw6,
    "PD1": pd1, "PD2": pd2, "PD3": pd3, "PD4": pd4, "PD5": pd5,
    "QT1": qt1, "QT3": qt3, "QT4": qt4,
    "TR1": tr1, "TR2": tr2, "TR3": tr3, "TR4": tr4, "TR5": tr5, "TR6": tr6,
    "IM1": im1, "IM2": im2, "IM3": im3, "IM4": im4, "IM5": im5, "IM6": im6, "IM7": im7,
}
