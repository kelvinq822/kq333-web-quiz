"""Expression tree for the Math 1.4 app.

Deliberately tiny: Num, Sym, Add, Mul, Div, Pow, Sqrt, Cbrt, Func.
No algebraic simplification happens here; layout work lives in tidy.py.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction


class Node:
    __slots__ = ()


@dataclass(frozen=True)
class Num(Node):
    v: Fraction

    def __post_init__(self):
        object.__setattr__(self, "v", Fraction(self.v))


@dataclass(frozen=True)
class Sym(Node):
    name: str


@dataclass(frozen=True)
class Add(Node):
    terms: tuple


@dataclass(frozen=True)
class Mul(Node):
    factors: tuple


@dataclass(frozen=True)
class Div(Node):
    num: Node
    den: Node


@dataclass(frozen=True)
class Pow(Node):
    base: Node
    exp: Fraction

    def __post_init__(self):
        object.__setattr__(self, "exp", Fraction(self.exp))


@dataclass(frozen=True)
class Sqrt(Node):
    arg: Node


@dataclass(frozen=True)
class Cbrt(Node):
    arg: Node


@dataclass(frozen=True)
class Func(Node):
    name: str
    arg: Node


ZERO = Num(Fraction(0))
ONE = Num(Fraction(1))
X = Sym("x")
Y = Sym("y")
DYDX = Sym("dy/dx")

TRIG = ("sin", "cos", "tan", "cot", "sec", "csc")


def num(v) -> Num:
    return Num(Fraction(v))


def add(*terms) -> Node:
    flat = []
    for t in terms:
        if isinstance(t, Add):
            flat.extend(t.terms)
        elif isinstance(t, Num) and t.v == 0:
            continue
        else:
            flat.append(t)
    if not flat:
        return ZERO
    if len(flat) == 1:
        return flat[0]
    return Add(tuple(flat))


def mul(*factors) -> Node:
    flat = []
    for f in factors:
        if isinstance(f, Mul):
            flat.extend(f.factors)
        elif isinstance(f, Num) and f.v == 0:
            return ZERO
        elif isinstance(f, Num) and f.v == 1:
            continue
        else:
            flat.append(f)
    if not flat:
        return ONE
    if len(flat) == 1:
        return flat[0]
    return Mul(tuple(flat))


def div(a, b) -> Node:
    return Div(a, b)


def power(base, exp) -> Pow:
    return Pow(base, Fraction(exp))


def sqrt(arg) -> Sqrt:
    return Sqrt(arg)


def cbrt(arg) -> Cbrt:
    return Cbrt(arg)


def fn(name, arg) -> Func:
    return Func(name, arg)


def neg(n) -> Node:
    return mul(Num(Fraction(-1)), n)


# ---------------------------------------------------------------- evaluation

def _check_finite(v: float) -> float:
    if not math.isfinite(v):
        raise ValueError("non-finite")
    return v


def evaluate(n: Node, x: float | None = None, y: float | None = None) -> float:
    """Numeric value. Raises ValueError when undefined / non-real."""
    if isinstance(n, Num):
        return float(n.v)
    if isinstance(n, Sym):
        if n.name == "x":
            if x is None:
                raise ValueError("x missing")
            return float(x)
        if n.name == "y":
            if y is None:
                raise ValueError("y missing")
            return float(y)
        raise ValueError("cannot evaluate %s" % n.name)
    if isinstance(n, Add):
        return _check_finite(sum(evaluate(t, x, y) for t in n.terms))
    if isinstance(n, Mul):
        out = 1.0
        for f in n.factors:
            out *= evaluate(f, x, y)
        return _check_finite(out)
    if isinstance(n, Div):
        d = evaluate(n.den, x, y)
        if abs(d) < 1e-12:
            raise ValueError("division by zero")
        return _check_finite(evaluate(n.num, x, y) / d)
    if isinstance(n, Pow):
        b = evaluate(n.base, x, y)
        e = float(n.exp)
        if b < 0 and abs(e - round(e)) > 1e-12:
            raise ValueError("negative base with fractional power")
        if b == 0 and e < 0:
            raise ValueError("zero to negative power")
        return _check_finite(b ** e)
    if isinstance(n, Sqrt):
        a = evaluate(n.arg, x, y)
        if a < 0:
            raise ValueError("sqrt of negative")
        return _check_finite(math.sqrt(a))
    if isinstance(n, Cbrt):
        a = evaluate(n.arg, x, y)
        return _check_finite(math.copysign(abs(a) ** (1.0 / 3.0), a))
    if isinstance(n, Func):
        a = evaluate(n.arg, x, y)
        if n.name == "sin":
            return _check_finite(math.sin(a))
        if n.name == "cos":
            return _check_finite(math.cos(a))
        if n.name == "tan":
            if abs(math.cos(a)) < 1e-12:
                raise ValueError("tan undefined")
            return _check_finite(math.tan(a))
        if n.name == "cot":
            if abs(math.sin(a)) < 1e-12:
                raise ValueError("cot undefined")
            return _check_finite(1.0 / math.tan(a))
        if n.name == "sec":
            if abs(math.cos(a)) < 1e-12:
                raise ValueError("sec undefined")
            return _check_finite(1.0 / math.cos(a))
        if n.name == "csc":
            if abs(math.sin(a)) < 1e-12:
                raise ValueError("csc undefined")
            return _check_finite(1.0 / math.sin(a))
        raise ValueError("unknown function %s" % n.name)
    raise TypeError("not a node: %r" % (n,))


def depends_on(n: Node, name: str) -> bool:
    if isinstance(n, Sym):
        return n.name == name
    if isinstance(n, (Num,)):
        return False
    if isinstance(n, Add):
        return any(depends_on(t, name) for t in n.terms)
    if isinstance(n, Mul):
        return any(depends_on(f, name) for f in n.factors)
    if isinstance(n, Div):
        return depends_on(n.num, name) or depends_on(n.den, name)
    if isinstance(n, Pow):
        return depends_on(n.base, name)
    if isinstance(n, (Sqrt, Cbrt)):
        return depends_on(n.arg, name)
    if isinstance(n, Func):
        return depends_on(n.arg, name)
    return False


def to_plain(n: Node) -> str:
    """Debug/plain-text rendering (tests, logs)."""
    if isinstance(n, Num):
        return str(n.v)
    if isinstance(n, Sym):
        return n.name
    if isinstance(n, Add):
        return "(" + " + ".join(to_plain(t) for t in n.terms) + ")"
    if isinstance(n, Mul):
        return "(" + "*".join(to_plain(f) for f in n.factors) + ")"
    if isinstance(n, Div):
        return "(%s)/(%s)" % (to_plain(n.num), to_plain(n.den))
    if isinstance(n, Pow):
        return "(%s)^%s" % (to_plain(n.base), n.exp)
    if isinstance(n, Sqrt):
        return "sqrt(%s)" % to_plain(n.arg)
    if isinstance(n, Cbrt):
        return "cbrt(%s)" % to_plain(n.arg)
    if isinstance(n, Func):
        return "%s(%s)" % (n.name, to_plain(n.arg))
    return "?"


@dataclass(frozen=True)
class Eq:
    """Implicit answer: derivative of both sides, left unsolved."""

    lhs: Node
    rhs: Node
