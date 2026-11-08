"""JSON API."""
from __future__ import annotations

import random
import time

from flask import Blueprint, current_app, jsonify, request, session

import services.leaderboard as leaderboard
import services.pending as pending
from services import ratelimit, users
from services.generator import GenerationError, build_question

from .helpers import (
    api_login_required,
    current_uid,
    me_payload,
    public_question_payload,
    store,
)

bp = Blueprint("api", __name__, url_prefix="/api")


def _limit(key_prefix, limit, window):
    ident = current_uid() or request.remote_addr or "anon"
    return ratelimit.allow("%s:%s" % (key_prefix, ident), limit, window)


@bp.post("/login")
def api_login():
    if not _limit("login", current_app.config["LOGIN_LIMIT_PER_HOUR"], 3600):
        return jsonify(error="rate_limited", message="嘗試太頻繁，請稍後再試"), 429
    data = request.get_json(silent=True) or {}
    try:
        profile = users.login_or_register(store(), data.get("name", ""))
    except users.NameError_ as exc:
        return jsonify(error="username_invalid", message=str(exc)), 422
    session.clear()
    session.permanent = True
    session["uid"] = profile["uid"]
    session["name"] = profile["username"]
    return jsonify(ok=True, **me_payload(store(), profile))


@bp.post("/logout")
def api_logout():
    session.clear()
    return jsonify(ok=True)


@bp.get("/question")
@api_login_required
def api_question():
    if not _limit("q", current_app.config["RATE_LIMIT_PER_MINUTE"], 60):
        return jsonify(error="rate_limited", message="請求太頻密"), 429
    uid = current_uid()
    try:
        question = build_question(random.Random())
    except GenerationError:
        return jsonify(error="generation_failed", message="暫時無法出題，請重試"), 503
    pending.save(store(), question, uid)
    pending.cleanup(store())
    return jsonify(public_question_payload(question))


@bp.post("/answer")
@api_login_required
def api_answer():
    if not _limit("a", current_app.config["RATE_LIMIT_PER_MINUTE"], 60):
        return jsonify(error="rate_limited", message="請求太頻密"), 429

    uid = current_uid()
    data = request.get_json(silent=True) or {}
    qid = str(data.get("qid", ""))
    try:
        choice = int(data.get("choice", -1))
        ms = int(data.get("ms", 0))
    except (TypeError, ValueError):
        return jsonify(error="bad_request", message="參數錯誤"), 400
    if choice < 0 or choice > 3:
        return jsonify(error="bad_request", message="選項超出範圍"), 400
    if ms < 0:
        ms = 0

    question = pending.load(store(), qid)
    if not question:
        return jsonify(error="question_not_found", message="題目已過期或已作答"), 404
    if question.get("uid") != uid:
        return jsonify(error="wrong_user", message="這不是你的題目"), 403
    if not pending.consume(store(), qid):
        return jsonify(error="already_answered", message="這題已作答"), 409

    min_ms = current_app.config["MIN_ANSWER_MS"]
    too_fast = ms < min_ms

    correct, points, profile, _entry = users.record_answer(
        store(), uid, question, choice, ms, award=not too_fast
    )

    leaderboard.invalidate()

    reply = {
        "ok": correct,
        "correct_index": question["answer_index"],
        "your_index": choice,
        "points": points,
        "too_fast": too_fast,
        "score": profile.get("points", 0),
        "streak": profile.get("streak", 0),
        "day_attempts": profile.get("day_attempts", 0),
        "nota": bool(question.get("nota")),
        "reveal_tex": question.get("answer_tex") if question["answer_index"] == 3 else None,
    }

    # Pre-fetch the next question so the client can switch instantly.
    try:
        nxt = build_question(random.Random())
        pending.save(store(), nxt, uid)
        reply["next"] = public_question_payload(nxt)
    except GenerationError:
        reply["next"] = None

    return jsonify(reply)


@bp.get("/me")
@api_login_required
def api_me():
    profile = users.get_profile(store(), current_uid())
    if not profile:
        return jsonify(error="not_logged_in", message="請重新登入"), 401
    return jsonify(me_payload(store(), profile))


@bp.get("/wrongbook")
@api_login_required
def api_wrongbook():
    book = store().read_json(store().wrongbook_path(current_uid()), default=[])
    return jsonify(book if isinstance(book, list) else [])


@bp.delete("/wrongbook/<qid>")
@api_login_required
def api_wrongbook_delete(qid):
    ok = users.delete_wrong(store(), current_uid(), qid)
    if not ok:
        return jsonify(error="not_found", message="找不到這筆記錄"), 404
    return jsonify(ok=True)


@bp.get("/board")
@api_login_required
def api_board():
    rows = leaderboard.all_rows(store())
    rank, _row = leaderboard.rank_of(store(), current_uid())
    return jsonify(rank=rank, rows=rows[:50])


@bp.get("/health")
def api_health():
    return jsonify(ok=True, ts=int(time.time()))
