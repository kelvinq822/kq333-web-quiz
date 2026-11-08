# -*- coding: utf-8 -*-
"""End-to-end test of the HTTP layer using Flask's test client."""
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from config import Config  # noqa: E402


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret"
    MIN_ANSWER_MS = 0


@pytest.fixture()
def client():
    tmp = tempfile.mkdtemp(prefix="m14-")
    cfg = TestConfig()
    cfg.DATA_DIR = tmp
    app = create_app(cfg)
    with app.test_client() as c:
        yield c


def login(c, name="測試君"):
    res = c.post("/api/login", json={"name": name})
    assert res.status_code == 200, res.data
    return res.get_json()


def test_login_validation(client):
    assert client.post("/api/login", json={"name": "ab"}).status_code == 422
    assert client.post("/api/login", json={"name": "a b c"}).status_code == 422
    assert client.post("/api/login", json={"name": "考生4821"}).status_code == 200


def test_requires_login(client):
    assert client.get("/api/question").status_code == 401
    assert client.get("/").status_code == 302


def test_full_flow(client):
    me = login(client)
    assert me["points"] == 0

    q = client.get("/api/question").get_json()
    assert len(q["choices"]) == 4
    assert "answer_index" not in q

    res = client.post("/api/answer", json={"qid": q["qid"], "choice": 0, "ms": 5000})
    assert res.status_code == 200
    data = res.get_json()
    assert data["next"] is not None

    # replaying the same qid must fail
    assert client.post("/api/answer", json={"qid": q["qid"], "choice": 1, "ms": 5000}).status_code == 404

    q2 = data["next"]
    from services.filestore import Store

    store = Store(client.application.config["DATA_DIR"])
    stored = store.read_json(store.pending_path(q2["qid"]))
    res3 = client.post(
        "/api/answer",
        json={"qid": q2["qid"], "choice": stored["answer_index"], "ms": 5000},
    )
    assert res3.status_code == 200
    body = res3.get_json()
    assert body["ok"] is True
    assert body["points"] >= 1


def test_wrongbook_and_board(client):
    login(client, "阿明哥")
    q = client.get("/api/question").get_json()
    client.post("/api/answer", json={"qid": q["qid"], "choice": 3, "ms": 4000})

    book = client.get("/api/wrongbook").get_json()
    assert isinstance(book, list)

    board = client.get("/api/board").get_json()
    assert board["rows"][0]["name"] == "阿明哥"

    page = client.get("/board")
    assert page.status_code == 200
    assert "阿明哥".encode() in page.data


def test_cannot_answer_others_question(client):
    login(client, "甲同學")
    q = client.get("/api/question").get_json()
    client.post("/api/logout")
    login(client, "乙同學")
    res = client.post("/api/answer", json={"qid": q["qid"], "choice": 0, "ms": 3000})
    assert res.status_code == 403


def test_pages_render(client):
    login(client, "頁面測試")
    for path in ("/", "/wrongbook", "/board", "/me"):
        res = client.get(path)
        assert res.status_code == 200, path
