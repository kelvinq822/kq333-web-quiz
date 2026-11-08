"""MCQ assembly: distractors, validation, "none of the above" (v2.0 section 5)."""
from __future__ import annotations

import random

from exprlib.latex import to_latex
from exprlib.mutate import EXPLICIT_MUTATIONS, IMPLICIT_MUTATIONS
from exprlib.nodes import Eq
from exprlib.tidy import tidy

from .compare import differs, eq_node

NOTA_TEXT = "以上皆非"
NOTA_RATE = 0.35
NOTA_IS_ANSWER_RATE = 0.5
MAX_OPTION_DELTA = 0.15


def _length(obj) -> int:
    if isinstance(obj, Eq):
        return len(to_latex(obj.lhs)) + len(to_latex(obj.rhs)) + 3
    return len(to_latex(obj))


def _key(obj):
    return eq_node(obj) if isinstance(obj, Eq) else obj


def _collect(answer, points, implicit, rng):
    """Ordered candidate list: (code, family, obj).  Never equivalent to answer."""
    table = IMPLICIT_MUTATIONS if implicit else EXPLICIT_MUTATIONS
    correct = _key(answer)
    target_len = _length(answer)
    found = []
    seen = set()
    for code, family, fn in table:
        try:
            cand = fn(answer)
        except (ZeroDivisionError, ValueError, TypeError):
            continue
        if cand is None:
            continue
        try:
            cand = tidy(cand) if not isinstance(cand, Eq) else Eq(tidy(cand.lhs), tidy(cand.rhs))
        except (ValueError, ZeroDivisionError):
            continue
        k = _key(cand)
        if k == correct:
            continue
        text = to_latex(k)
        if text in seen:
            continue
        if not differs(k, correct, points, has_dydx=implicit):
            continue
        if not implicit:
            dl = _length(cand)
            if abs(dl - target_len) > max(10, MAX_OPTION_DELTA * target_len):
                continue
        seen.add(text)
        found.append((code, family, cand))
    return found


def build_options(answer, points, implicit, rng):
    """Return (choices, answer_index, codes, nota) or None when impossible."""
    found = _collect(answer, points, implicit, rng)

    has_nota = rng.random() < NOTA_RATE
    nota_correct = has_nota and rng.random() < NOTA_IS_ANSWER_RATE

    if nota_correct:
        picked = _pick_distinct(found, 3, rng)
        if picked is None:
            return None
        rng.shuffle(picked)
        options = [obj for _, _, obj in picked]
        codes = [code for code, _, _ in picked]
        choices = [to_latex(o) if not isinstance(o, Eq) else _eq_tex(o) for o in options]
        choices.append(NOTA_TEXT)
        return choices, 3, codes + ["none_of_above"], True

    need = 2 if has_nota else 3
    picked = _pick_distinct(found, need, rng)
    if picked is None:
        return None
    options = [answer] + [obj for _, _, obj in picked]
    codes = [None] + [code for code, _, _ in picked]
    order = list(range(len(options)))
    rng.shuffle(order)
    choices = []
    for i in order:
        o = options[i]
        choices.append(to_latex(o) if not isinstance(o, Eq) else _eq_tex(o))
    if has_nota:
        choices.append(NOTA_TEXT)
    answer_index = order.index(0)
    return choices, answer_index, [codes[i] for i in order] + (["none_of_above"] if has_nota else []), has_nota


def _eq_tex(eq: Eq) -> str:
    return "%s = %s" % (to_latex(eq.lhs), to_latex(eq.rhs))


def _pick_distinct(found, n, rng):
    """Pick n candidates, preferring distinct families, then fill up."""
    if len(found) < n:
        return None
    shuffled = found[:]
    rng.shuffle(shuffled)
    chosen = []
    families = set()
    for item in shuffled:
        if item[1] not in families:
            chosen.append(item)
            families.add(item[1])
            if len(chosen) == n:
                return chosen
    for item in shuffled:
        if item in chosen:
            continue
        chosen.append(item)
        if len(chosen) == n:
            return chosen
    return None
