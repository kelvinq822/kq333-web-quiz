"""Application configuration (environment driven)."""
from __future__ import annotations

import os
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    SECRET_KEY = os.environ.get("MATH14_SECRET") or "dev-only-secret-change-me"
    DATA_DIR = os.environ.get("MATH14_DATA") or os.path.join(BASE_DIR, "data")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("MATH14_SECURE", "0") == "1"
    PERMANENT_SESSION_LIFETIME = timedelta(days=90)
    JSON_AS_ASCII = False
    MAX_CONTENT_LENGTH = 8 * 1024

    # KaTeX is loaded from a CDN by default; scripts/fetch_katex.py can vendor it.
    KATEX_VERSION = "0.16.11"
    KATEX_CDN = "https://cdn.jsdelivr.net/npm/katex@%(version)s/dist/"
    USE_LOCAL_KATEX = os.environ.get("MATH14_LOCAL_KATEX", "0") == "1"

    RATE_LIMIT_PER_MINUTE = 120
    LOGIN_LIMIT_PER_HOUR = 10
    MIN_ANSWER_MS = 250
