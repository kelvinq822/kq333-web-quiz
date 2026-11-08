"""Question generation and quality gates (v2.0 sections 3.4, 4.6, 5.4)."""
from __future__ import annotations

import math
import random
import uuid
from dataclasses import dataclass, field
from fractions import Fraction

from exprlib.diff import diff
from exprlib.latex import to_latex
from exprlib.nodes import Eq, evaluate
from exprlib.tidy import tidy

from bank.templates import BUILDERS
from .compare import safe_eval
from .mcq import build_options

MAX_ANSWER_LEN = 150
MAX_ATTEMPTS = 80

TOPIC_WEIGHTS = {
    "power": 20,
    "product": 16,
    "quotient": 12,
    "trig": 20,
    "implicit": 24,
}

META = {
    "PW1": ("power", 1), "PW2": ("power", 1), "PW5": ("power", 2), "PW6": ("power", 3),
    "PD1": ("product", 2), "PD2": ("product", 2), "PD3": ("product", 2),
    "PD4": ("product", 2), "PD5": ("product", 3),
    "QT1": ("quotient", 2), "QT3": ("quotient", 2), "QT4": ("quotient", 2),
    "TR1": ("trig", 1), "TR2": ("trig", 2), "TR3": ("trig", 2),
    "TR4": ("trig", 2), "TR5": ("trig", 2), "TR6": ("trig", 3),
    "IM1": ("implicit", 2), "IM2": ("implicit", 3), "IM3": ("implicit", 3),
    "IM4": ("implicit", 3), "IM5": ("implicit", 3), "IM6": ("implicit", 3),
    "IM7": ("implicit", 3),
}

BY_TOPIC = {}
for _tid, (_topic, _) in META.items():
    BY_TOPIC.setdefault(_topic, []).append(_tid)


class GenerationError(RuntimeError):
    pass


@dataclass
class Question:
    qid: str
    tid: str
    topic: str
    difficulty: int
    stmt: str
    choices: list
    answer_index: int
    codes: list
    points: list
    nota: bool
    answer_tex: str
    implicit: bool


def _pick_topic(rng):
    topics = list(TOPIC_WEIGHTS)
    weights = [TOPIC_WEIGHTS[t] for t in topics]
    return rng.choices(topics, weights=weights, k=1)[0]


def _pick_template(rng, last=None):
    topic = _pick_topic(rng)
    pool = [t for t in BY_TOPIC[topic] if t != last] or BY_TOPIC[topic]
    return rng.choice(pool)


def _valid_explicit_points(expr, answer, xs):
    pts = []
    for x in xs:
        if safe_eval(expr, x) is None:
            continue
        if safe_eval(answer, x) is None:
            continue
        pts.append((x, None))
    return pts


def _valid_implicit_points(lhs, rhs, dlhs, drhs, pts):
    out = []
    for (x, y) in pts:
        left = safe_eval(lhs, x, y)
        right = safe_eval(rhs, x, y)
        if left is None or right is None:
            continue
        if abs(left - right) > 1e-6 * max(1.0, abs(left), abs(right)):
            continue
        ok = True
        for d in (0.7, -1.3):
            from .compare import subst_dydx

            if safe_eval(subst_dydx(dlhs, d), x, y) is None or safe_eval(subst_dydx(drhs, d), x, y) is None:
                ok = False
                break
        if ok:
            out.append((x, y))
    return out


def build_question(rng: random.Random = None, last_tid=None) -> Question:
    rng = rng or random.Random()
    last_error = None
    for _ in range(MAX_ATTEMPTS):
        tid = _pick_template(rng, last_tid)
        topic, difficulty = META[tid]
        try:
            built = BUILDERS[tid](rng)
        except (ZeroDivisionError, ValueError, OverflowError) as exc:  # bad params, retry
            last_error = exc
            continue

        implicit = built.lhs is not None
        if implicit:
            from .compare import eq_node

            answer = Eq(tidy(diff(built.lhs)), tidy(diff(built.rhs)))
            pts = _valid_implicit_points(built.lhs, built.rhs, answer.lhs, answer.rhs, built.points)
            key = eq_node(answer)
            answer_tex = "%s = %s" % (to_latex(answer.lhs), to_latex(answer.rhs))
        else:
            answer = tidy(diff(built.expr))
            pts = _valid_explicit_points(built.expr, answer, built.xs)
            key = answer
            answer_tex = to_latex(answer)

        if len(pts) < 3:
            continue
        if len(to_latex(key)) > MAX_ANSWER_LEN:
            continue

        options = build_options(answer, pts, implicit, rng)
        if options is None:
            continue
        choices, answer_index, codes, nota = options

        return Question(
            qid=uuid.uuid4().hex,
            tid=tid,
            topic=topic,
            difficulty=difficulty,
            stmt=built.stmt,
            choices=choices,
            answer_index=answer_index,
            codes=codes,
            points=pts,
            nota=nota,
            answer_tex=answer_tex,
            implicit=implicit,
        )
    raise GenerationError("could not generate a question: %r" % (last_error,))
