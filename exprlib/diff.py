"""Mechanical differentiation (v2.0 section 4.1).

Every rule is applied exactly as written in the spec; nothing is simplified.
"""
from __future__ import annotations

from fractions import Fraction

from .nodes import (
    Add,
    Cbrt,
    Div,
    DYDX,
    Func,
    Mul,
    Node,
    Num,
    ONE,
    Pow,
    Sqrt,
    Sym,
    ZERO,
    add,
    mul,
    num,
)


def _outer(name: str, a: Node) -> Node:
    """Derivative of the outer function, applied to a."""
    if name == "sin":
        return Func("cos", a)
    if name == "cos":
        return mul(num(-1), Func("sin", a))
    if name == "tan":
        return Pow(Func("sec", a), Fraction(2))
    if name == "cot":
        return mul(num(-1), Pow(Func("csc", a), Fraction(2)))
    if name == "sec":
        return mul(Func("sec", a), Func("tan", a))
    if name == "csc":
        return mul(num(-1), Func("csc", a), Func("cot", a))
    raise ValueError("unknown function %s" % name)


def diff(n: Node, wrt: str = "x") -> Node:
    if isinstance(n, Num):
        return ZERO
    if isinstance(n, Sym):
        if n.name == wrt:
            return ONE
        if n.name == "y" and wrt == "x":
            return DYDX
        return ZERO
    if isinstance(n, Add):
        return add(*[diff(t, wrt) for t in n.terms])
    if isinstance(n, Mul):
        parts = []
        for i, f in enumerate(n.factors):
            others = tuple(n.factors[:i]) + tuple(n.factors[i + 1:])
            if i == 0:
                parts.append(mul(diff(f, wrt), *others))
            else:
                parts.append(mul(*others, diff(f, wrt)))
        return add(*parts)
    if isinstance(n, Div):
        u, v = n.num, n.den
        return Div(
            add(mul(diff(u, wrt), v), mul(num(-1), u, diff(v, wrt))),
            Pow(v, Fraction(2)),
        )
    if isinstance(n, Pow):
        return mul(num(n.exp), Pow(n.base, n.exp - 1), diff(n.base, wrt))
    if isinstance(n, Sqrt):
        return Div(diff(n.arg, wrt), mul(num(2), Sqrt(n.arg)))
    if isinstance(n, Cbrt):
        return mul(num(Fraction(1, 3)), Pow(n.arg, Fraction(-2, 3)), diff(n.arg, wrt))
    if isinstance(n, Func):
        return mul(_outer(n.name, n.arg), diff(n.arg, wrt))
    raise TypeError("cannot differentiate %r" % (n,))
