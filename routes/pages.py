"""HTML pages."""
from __future__ import annotations

import random

from flask import Blueprint, redirect, render_template, session, url_for

import services.leaderboard as leaderboard
import services.pending as pending
from services import users
from services.generator import GenerationError, build_question

from .helpers import current_profile, current_uid, me_payload, public_question_payload, store

bp = Blueprint("pages", __name__)


@bp.get("/login")
def login():
    if current_uid():
        return redirect(url_for("pages.index"))
    return render_template("login.html")


@bp.get("/")
def index():
    uid = current_uid()
    if not uid:
        return redirect(url_for("pages.login"))
    profile = current_profile()
    if not profile:
        session.clear()
        return redirect(url_for("pages.login"))

    try:
        question = build_question(random.Random())
        pending.save(store(), question, uid)
        pending.cleanup(store())
        payload = public_question_payload(question)
    except GenerationError:
        payload = None

    return render_template(
        "index.html",
        question=payload,
        me=me_payload(store(), profile),
    )


@bp.get("/wrongbook")
def wrongbook():
    uid = current_uid()
    if not uid:
        return redirect(url_for("pages.login"))
    book = store().read_json(store().wrongbook_path(uid), default=[])
    if not isinstance(book, list):
        book = []
    return render_template("wrongbook.html", book=book, me=me_payload(store(), current_profile()))


@bp.get("/board")
def board():
    uid = current_uid()
    if not uid:
        return redirect(url_for("pages.login"))
    rows = leaderboard.all_rows(store())
    rank, me_row = leaderboard.rank_of(store(), uid)
    return render_template(
        "board.html",
        rows=rows[:50],
        rank=rank,
        me_row=me_row,
        me=me_payload(store(), current_profile()),
    )


@bp.get("/me")
def me():
    uid = current_uid()
    if not uid:
        return redirect(url_for("pages.login"))
    return render_template("me.html", me=me_payload(store(), current_profile()))
