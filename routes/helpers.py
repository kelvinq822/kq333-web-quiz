"""Shared request helpers for the web layer."""
from __future__ import annotations

from functools import wraps

from flask import current_app, jsonify, session

import services.leaderboard as leaderboard
from services import users


def store():
    return current_app.extensions["store"]


def current_uid():
    return session.get("uid")


def current_profile():
    uid = current_uid()
    if not uid:
        return None
    return users.get_profile(store(), uid)


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_uid():
            if current_app.request_class is not None and _wants_json():
                return jsonify(error="not_logged_in", message="請先登入"), 401
            from flask import redirect, url_for

            return redirect(url_for("pages.login"))
        return view(*args, **kwargs)

    return wrapper


def api_login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_uid():
            return jsonify(error="not_logged_in", message="請先登入"), 401
        return view(*args, **kwargs)

    return wrapper


def _wants_json() -> bool:
    from flask import request

    return request.path.startswith("/api/")


def public_question_payload(q):
    return {
        "qid": q.qid,
        "stmt_tex": q.stmt,
        "choices": q.choices,
        "topic": q.topic,
        "difficulty": q.difficulty,
        "nota": q.nota,
    }


def me_payload(store_, profile):
    rank, _row = leaderboard.rank_of(store_, profile["uid"])
    return {
        "name": profile["username"],
        "points": profile.get("points", 0),
        "rank": rank,
        "correct": profile.get("correct", 0),
        "attempts": profile.get("attempts", 0),
        "streak": profile.get("streak", 0),
        "day_attempts": profile.get("day_attempts", 0),
    }
