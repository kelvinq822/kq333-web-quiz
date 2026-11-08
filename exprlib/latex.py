"""LaTeX rendering.

Rules follow v2.0 section 4: a single fraction line, radicals kept as
radicals, powers written as powers.  This module never rewrites maths -- it
only decides where to put brackets.
"""
from __future__ import annotations

from fractions import Fraction

from .nodes import Add, Cbrt, Div, Eq, Func, Mul, Node, Num, Pow, Sqrt, Sym

_FUNC_LATEX = {
    "sin": r"\sin",
    "cos": r"\cos",
    "tan": r"\tan",
    "cot": r"\cot",
    "sec": r"\sec",
    "csc": r"\csc",
}


def _is_neg(n: Node) -> bool:
    if isinstance(n, Num):
        return n.v < 0
    if isinstance(n, Mul) and n.factors and isinstance(n.factors[0], Num):
        return n.factors[0].v < 0
    return False


def _strip_neg(n: Node) -> Node:
    if isinstance(n, Num):
        return Num(-n.v)
    if isinstance(n, Mul) and n.factors and isinstance(n.factors[0], Num):
        c = -n.factors[0].v
        rest = tuple(n.factors[1:])
        if c == 1:
            return rest[0] if len(rest) == 1 else Mul(rest)
        return Mul((Num(c),) + rest)
    return n


def _exp_text(exp: Fraction) -> str:
    if exp.denominator == 1:
        return str(exp.numerator)
    sign = "-" if exp < 0 else ""
    num = abs(exp.numerator)
    return "%s%d/%d" % (sign, num, exp.denominator)


def _num_text(v: Fraction) -> str:
    if v.denominator == 1:
        return str(v.numerator)
    sign = "-" if v < 0 else ""
    return "%s\\frac{%d}{%d}" % (sign, abs(v.numerator), v.denominator)


def _needs_parens(n: Node, as_base: bool = True) -> bool:
    if isinstance(n, Add):
        return True
    if isinstance(n, Mul):
        return True
    if isinstance(n, Div):
        return True
    if isinstance(n, Num) and n.v < 0:
        return True
    if isinstance(n, Pow) and as_base:
        return True
    return False


def _l(n: Node) -> str:
    if isinstance(n, Num):
        return _num_text(n.v)
    if isinstance(n, Sym):
        if n.name == "dy/dx":
            return r"\frac{dy}{dx}"
        return n.name
    if isinstance(n, Add):
        out = []
        for i, t in enumerate(n.terms):
            neg = _is_neg(t)
            body = _l(_strip_neg(t) if neg else t)
            if i == 0:
                out.append(("-" if neg else "") + body)
            else:
                out.append((" - " if neg else " + ") + body)
        return "".join(out)
    if isinstance(n, Mul):
        parts = []
        prev = None
        first = True
        for f in n.factors:
            if first and isinstance(f, Num) and f.v == -1:
                parts.append("-")
                first = False
                continue
            s = _l(f)
            if isinstance(f, Add):
                s = r"\left(%s\right)" % s
            if prev is not None and isinstance(prev, Sym) and isinstance(f, Sym):
                if prev.name == f.name:
                    # "x x" would read as one token; everything else juxtaposes
                    s = r"\cdot " + s
            parts.append(s)
            prev = f
            first = False
        return "".join(parts)
    if isinstance(n, Div):
        return r"\frac{%s}{%s}" % (_l(n.num), _l(n.den))
    if isinstance(n, Pow):
        base = n.base
        if isinstance(base, Func):
            macro = _FUNC_LATEX[base.name]
            return "%s^{%s}%s" % (
                macro,
                _exp_text(n.exp),
                _func_arg(base.arg),
            )
        b = _l(base)
        if _needs_parens(base):
            b = r"\left(%s\right)" % b
        return "%s^{%s}" % (b, _exp_text(n.exp))
    if isinstance(n, Sqrt):
        return r"\sqrt{%s}" % _l(n.arg)
    if isinstance(n, Cbrt):
        return r"\sqrt[3]{%s}" % _l(n.arg)
    if isinstance(n, Func):
        return "%s%s" % (_FUNC_LATEX[n.name], _func_arg(n.arg))
    raise TypeError("cannot render %r" % (n,))


def _func_arg(n: Node) -> str:
    if isinstance(n, Sym):
        return " " + n.name
    return "\\left(%s\\right)" % _l(n)


def to_latex(n: Node, display_style: bool = False) -> str:
    s = _l(n)
    if display_style:
        return s.replace(r"\frac", r"\dfrac")
    return s


def eq_to_latex(eq: Eq, display_style: bool = False) -> str:
    return "%s = %s" % (
        to_latex(eq.lhs, display_style),
        to_latex(eq.rhs, display_style),
    )


def display_len(n: Node) -> int:
    return len(to_latex(n))
