"""Distractor generation by structural mutation (v2.0 section 5).

Every mutation returns a *different* expression, or None when it does not
apply.  Nothing here is trusted: services.mcq validates each candidate
numerically before it can become an option.
"""
from __future__ import annotations

from fractions import Fraction

from .diff import diff
from .nodes import (
    Add,
    Cbrt,
    Div,
    DYDX,
    Eq,
    Func,
    Mul,
    Node,
    Num,
    ONE,
    Pow,
    Sqrt,
    Sym,
)
from .tidy import tidy

_NO = object()


# ----------------------------------------------------------------- walking

def _walk(n: Node, rule):
    """Pre-order rewrite.  rule(n) returns a node or _NO."""
    r = rule(n)
    if r is not _NO:
        return r
    if isinstance(n, Add):
        for i, t in enumerate(n.terms):
            r = _walk(t, rule)
            if r is not _NO:
                return Add(n.terms[:i] + (r,) + n.terms[i + 1:])
    elif isinstance(n, Mul):
        for i, f in enumerate(n.factors):
            r = _walk(f, rule)
            if r is not _NO:
                return Mul(n.factors[:i] + (r,) + n.factors[i + 1:])
    elif isinstance(n, Div):
        r = _walk(n.num, rule)
        if r is not _NO:
            return Div(r, n.den)
        r = _walk(n.den, rule)
        if r is not _NO:
            return Div(n.num, r)
    elif isinstance(n, Pow):
        r = _walk(n.base, rule)
        if r is not _NO:
            return Pow(r, n.exp)
    elif isinstance(n, (Sqrt, Cbrt)):
        r = _walk(n.arg, rule)
        if r is not _NO:
            return type(n)(r)
    elif isinstance(n, Func):
        r = _walk(n.arg, rule)
        if r is not _NO:
            return Func(n.name, r)
    return _NO


def _neg(n: Node) -> Node:
    if isinstance(n, Num):
        return Num(-n.v)
    if isinstance(n, Mul) and n.factors and isinstance(n.factors[0], Num):
        return Mul((Num(-n.factors[0].v),) + n.factors[1:])
    if isinstance(n, Add):
        return Add(tuple(_neg(t) for t in n.terms))
    if isinstance(n, Div):
        return Div(_neg(n.num), n.den)
    return Mul((Num(Fraction(-1)), n))


def contains_dydx(n: Node) -> bool:
    if isinstance(n, Sym):
        return n.name == "dy/dx"
    if isinstance(n, Num):
        return False
    if isinstance(n, Add):
        return any(contains_dydx(t) for t in n.terms)
    if isinstance(n, Mul):
        return any(contains_dydx(f) for f in n.factors)
    if isinstance(n, Div):
        return contains_dydx(n.num) or contains_dydx(n.den)
    if isinstance(n, Pow):
        return contains_dydx(n.base)
    if isinstance(n, (Sqrt, Cbrt)):
        return contains_dydx(n.arg)
    if isinstance(n, Func):
        return contains_dydx(n.arg)
    return False


def has_func(n: Node, names) -> bool:
    r = _walk(n, lambda x: Num(1) if isinstance(x, Func) and x.name in names else _NO)
    return r is not _NO


# --------------------------------------------------------------- explicit

def m_sign_outer(n: Node) -> Node:
    return _neg(n)


def m_pow_plus_one(n: Node) -> Node:
    def rule(x):
        if isinstance(x, Pow) and x.exp.denominator == 1 and 1 <= abs(x.exp) <= 6:
            step = 1 if x.exp > 0 else -1
            return Pow(x.base, x.exp + step)
        return _NO

    r = _walk(n, rule)
    return None if r is _NO else r


def m_pow_minus_one(n: Node) -> Node:
    def rule(x):
        if isinstance(x, Pow) and x.exp.denominator == 1 and 2 <= abs(x.exp) <= 7:
            step = 1 if x.exp > 0 else -1
            return Pow(x.base, x.exp - step)
        return _NO

    r = _walk(n, rule)
    return None if r is _NO else r


def m_coeff_drop(n: Node) -> Node:
    def rule(x):
        if isinstance(x, Mul) and x.factors and isinstance(x.factors[0], Num):
            c = x.factors[0].v
            if c != 0 and abs(c) != 1:
                sign = Fraction(1) if c > 0 else Fraction(-1)
                rest = x.factors[1:]
                if not rest:
                    return Num(sign)
                return Mul((Num(sign),) + rest)
        return _NO

    r = _walk(n, rule)
    return None if r is _NO else r


def m_arg_scale(n: Node) -> Node:
    def rule(x):
        if isinstance(x, Func) and isinstance(x.arg, Mul):
            k = x.arg.factors[0]
            if isinstance(k, Num) and k.v != 0 and abs(k.v) != 1:
                rest = x.arg.factors[1:]
                new_arg = rest[0] if len(rest) == 1 else Mul(rest)
                return Func(x.name, new_arg)
        return _NO

    r = _walk(n, rule)
    return None if r is _NO else r


def m_trig_swap(n: Node) -> Node:
    def rule(x):
        if isinstance(x, Pow) and isinstance(x.base, Func) and x.exp == 2:
            if x.base.name == "csc":
                return Pow(Func("sec", x.base.arg), 2)
            if x.base.name == "sec":
                return Pow(Func("csc", x.base.arg), 2)
        if isinstance(x, Func):
            if x.name == "tan":
                return Func("cot", x.arg)
            if x.name == "cot":
                return Func("tan", x.arg)
            if x.name == "sin":
                return Func("cos", x.arg)
            if x.name == "cos":
                return Func("sin", x.arg)
        return _NO

    r = _walk(n, rule)
    return None if r is _NO else r


def m_trig_sign(n: Node) -> Node:
    def rule(x):
        if isinstance(x, Mul) and x.factors and isinstance(x.factors[0], Num):
            if has_func(x, ("csc", "cot")):
                return Mul((Num(-x.factors[0].v),) + x.factors[1:])
        return _NO

    r = _walk(n, rule)
    return None if r is _NO else r


def m_root_factor(n: Node) -> Node:
    def rule(x):
        if isinstance(x, Mul) and x.factors and isinstance(x.factors[0], Num):
            if any(isinstance(f, Pow) and f.exp.denominator != 1 for f in x.factors[1:]):
                c = x.factors[0].v
                newc = c * 2 if c != 0 else Fraction(2)
                return Mul((Num(newc),) + x.factors[1:])
        return _NO

    r = _walk(n, rule)
    return None if r is _NO else r


def m_second_derivative(n: Node) -> Node:
    return tidy(diff(n))


EXPLICIT_MUTATIONS = [
    ("sign_outer", "structure", m_sign_outer),
    ("pow_off_by_one", "power", m_pow_plus_one),
    ("pow_off_by_one_low", "power", m_pow_minus_one),
    ("coeff_drop", "coeff", m_coeff_drop),
    ("arg_scale", "coeff", m_arg_scale),
    ("trig_swap", "trig", m_trig_swap),
    ("trig_sign", "trig", m_trig_sign),
    ("root_factor", "root", m_root_factor),
    ("second_derivative", "structure", m_second_derivative),
]


# --------------------------------------------------------------- implicit

def _eq_map(eq: Eq, rule):
    left = _walk(eq.lhs, rule)
    if left is not _NO:
        return Eq(left, eq.rhs)
    right = _walk(eq.rhs, rule)
    if right is not _NO:
        return Eq(eq.lhs, right)
    return None


def im_dy_drop(eq: Eq):
    return _eq_map(eq, lambda x: ONE if isinstance(x, Sym) and x.name == "dy/dx" else _NO)


def im_dy_square(eq: Eq):
    return _eq_map(eq, lambda x: Pow(DYDX, 2) if isinstance(x, Sym) and x.name == "dy/dx" else _NO)


def im_drop_dy_term(eq: Eq):
    def rule(x):
        if isinstance(x, Add):
            for i, t in enumerate(x.terms):
                if contains_dydx(t):
                    rest = x.terms[:i] + x.terms[i + 1:]
                    if rest:
                        return rest[0] if len(rest) == 1 else Add(rest)
        return _NO

    return _eq_map(eq, rule)


def im_flip_dy_term(eq: Eq):
    def rule(x):
        if isinstance(x, Add):
            for i, t in enumerate(x.terms):
                if contains_dydx(t):
                    new = list(x.terms)
                    new[i] = _neg(t)
                    return Add(tuple(new))
        return _NO

    return _eq_map(eq, rule)


def im_neg_lhs(eq: Eq):
    return Eq(_neg(eq.lhs), eq.rhs)


def im_trig_sign(eq: Eq):
    def rule(x):
        if isinstance(x, Mul) and x.factors and isinstance(x.factors[0], Num):
            if has_func(x, ("csc", "cot", "sec", "tan")):
                return Mul((Num(-x.factors[0].v),) + x.factors[1:])
        return _NO

    return _eq_map(eq, rule)


def im_pow_off_by_one(eq: Eq):
    def rule(x):
        if isinstance(x, Pow) and x.exp.denominator == 1 and 1 <= x.exp <= 6:
            return Pow(x.base, x.exp + 1)
        return _NO

    return _eq_map(eq, rule)


def im_term_no_dy(eq: Eq):
    """Forget dy/dx on a single product term (the other terms keep it)."""

    def rule(x):
        if isinstance(x, Mul):
            has = any(isinstance(f, Sym) and f.name == "dy/dx" for f in x.factors)
            if has:
                rest = tuple(f for f in x.factors if not (isinstance(f, Sym) and f.name == "dy/dx"))
                if rest:
                    return rest[0] if len(rest) == 1 else Mul(rest)
        return _NO

    return _eq_map(eq, rule)


IMPLICIT_MUTATIONS = [
    ("imp_product_second_missing", "product", im_drop_dy_term),
    ("imp_product_no_dy", "product", im_dy_drop),
    ("imp_product_term_no_dy", "product", im_term_no_dy),
    ("imp_product_sign", "product", im_flip_dy_term),
    ("imp_chain_extra", "chain", im_dy_square),
    ("imp_trig_sign", "trig", im_trig_sign),
    ("imp_pow_off_by_one", "power", im_pow_off_by_one),
    ("sign_outer", "structure", im_neg_lhs),
]
