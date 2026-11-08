"""Layout-only tidy pass (v2.0 section 4.2, rules T1-T5).

What it does:
  T1 fold numeric arithmetic (constants, including exponents)
  T2 drop multiplicative 1 (and x^1, x^0)
  T3 put the numeric coefficient first
  T4 keep a single fraction line (a product containing a fraction becomes one)
  T5 keep term order as produced by the differentiation rules

What it never does: collect like terms, expand products, cancel symbolic
factors, rewrite radicals as powers, or solve for dy/dx.
"""
from __future__ import annotations

from fractions import Fraction

from .nodes import (
    Add,
    Cbrt,
    Div,
    Func,
    Mul,
    Node,
    Num,
    ONE,
    Pow,
    Sqrt,
    Sym,
    ZERO,
)


def _rank(n: Node) -> int:
    if isinstance(n, Sym):
        return 9 if n.name == "dy/dx" else 0
    if isinstance(n, Num):
        return 1
    if isinstance(n, Pow):
        return 2
    if isinstance(n, Func):
        return 3
    if isinstance(n, (Sqrt, Cbrt)):
        return 4
    if isinstance(n, Div):
        return 5
    return 6


def _split_coef(n: Node):
    if isinstance(n, Num):
        return n.v, ONE
    if isinstance(n, Mul) and n.factors and isinstance(n.factors[0], Num):
        rest = tuple(n.factors[1:])
        return n.factors[0].v, (rest[0] if len(rest) == 1 else Mul(rest))
    return Fraction(1), n


def _add(terms) -> Node:
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


def _mul(factors) -> Node:
    flat = []
    coef = Fraction(1)
    dens = []
    for f in factors:
        if isinstance(f, Mul):
            flat.extend(f.factors)
        elif isinstance(f, Div):
            flat.append(f.num)
            dens.append(f.den)
        elif isinstance(f, Num):
            coef *= f.v
        else:
            flat.append(f)
    if coef == 0:
        return ZERO

    if dens:
        num_node = _mul(flat) if flat else ONE
        den_node = _mul(dens) if len(dens) > 1 else dens[0]
        return _div(_apply_coef(coef, num_node), den_node)

    flat.sort(key=_rank)
    if not flat:
        return Num(coef) if coef != 1 else ONE
    body = flat[0] if len(flat) == 1 else Mul(tuple(flat))
    return _apply_coef(coef, body)


def _apply_coef(coef: Fraction, node: Node) -> Node:
    if coef == 1:
        return node
    if node is ONE:
        return Num(coef)
    if isinstance(node, Num):
        return Num(node.v * coef)
    if isinstance(node, Mul):
        return Mul((Num(coef),) + tuple(node.factors))
    return Mul((Num(coef), node))


def _div(a: Node, b: Node) -> Node:
    if isinstance(a, Num) and a.v == 0:
        return ZERO
    if isinstance(b, Num):
        if b.v == 0:
            raise ZeroDivisionError("division by zero in tidy")
        if b.v == 1:
            return a
        if isinstance(a, Num):
            return Num(a.v / b.v)
        if isinstance(a, Mul) and isinstance(a.factors[0], Num):
            c = a.factors[0].v / b.v
            rest = tuple(a.factors[1:])
            base = rest[0] if len(rest) == 1 else Mul(rest)
            return _mul([Num(c), base])
        return Div(a, b)

    ca, ra = _split_coef(a)
    cb, rb = _split_coef(b)
    if cb == 0:
        raise ZeroDivisionError("division by zero in tidy")
    coef = ca / cb

    num_parts = []
    if coef.denominator != 1:
        num_parts.append(Num(coef.numerator))
        den_parts = [Num(coef.denominator)]
    else:
        if coef != 1:
            num_parts.append(Num(coef))
        den_parts = []

    if ra is not ONE:
        num_parts.append(ra)
    if rb is not ONE:
        den_parts.append(rb)

    num_node = ONE if not num_parts else (num_parts[0] if len(num_parts) == 1 else Mul(tuple(num_parts)))
    den_node = ONE if not den_parts else (den_parts[0] if len(den_parts) == 1 else Mul(tuple(den_parts)))
    if den_node is ONE:
        return num_node
    return Div(num_node, den_node)


def _pow(base: Node, exp: Fraction) -> Node:
    if exp == 1:
        return base
    if exp == 0:
        return ONE
    if isinstance(base, Num):
        if base.v == 1:
            return ONE
        if exp.denominator == 1:
            return Num(base.v ** int(exp))
        return Pow(base, exp)
    if isinstance(base, Pow):
        return _pow(base.base, base.exp * exp)
    return Pow(base, exp)


def _t(n: Node) -> Node:
    if isinstance(n, (Num, Sym)):
        return n
    if isinstance(n, Add):
        return _add([_t(t) for t in n.terms])
    if isinstance(n, Mul):
        return _mul([_t(f) for f in n.factors])
    if isinstance(n, Div):
        return _div(_t(n.num), _t(n.den))
    if isinstance(n, Pow):
        return _pow(_t(n.base), n.exp)
    if isinstance(n, Sqrt):
        return Sqrt(_t(n.arg))
    if isinstance(n, Cbrt):
        return Cbrt(_t(n.arg))
    if isinstance(n, Func):
        return Func(n.name, _t(n.arg))
    raise TypeError("cannot tidy %r" % (n,))


def tidy(n: Node) -> Node:
    for _ in range(5):
        m = _t(n)
        if m == n:
            return m
        n = m
    return n
