"""Lightweight backend translations for API responses and AI prompts."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = {"en", "fr", "es", "ar", "pt", "sw", "ha", "yo", "ig"}
LOCALES_DIR = Path(__file__).resolve().parents[1] / "locales"


def normalize_language(lang: str | None) -> str:
    code = (lang or DEFAULT_LANGUAGE).split("-")[0].lower()
    return code if code in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


@lru_cache(maxsize=len(SUPPORTED_LANGUAGES))
def load_translations(lang: str) -> dict[str, str]:
    code = normalize_language(lang)
    path = LOCALES_DIR / f"{code}.json"
    if not path.exists() and code != DEFAULT_LANGUAGE:
        path = LOCALES_DIR / f"{DEFAULT_LANGUAGE}.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def t(key: str, lang: str | None = DEFAULT_LANGUAGE, **params: Any) -> str:
    code = normalize_language(lang)
    translations = load_translations(code)
    fallback = load_translations(DEFAULT_LANGUAGE)
    text = translations.get(key) or fallback.get(key) or key
    return text.format(**params) if params else text


def user_language(user: Any) -> str:
    preferences = getattr(user, "preferences", None) or {}
    language = preferences.get("language")
    if language:
        return normalize_language(language)
    user_language_model = getattr(user, "language", None)
    return normalize_language(getattr(user_language_model, "code", None))


def user_currency(user: Any) -> str:
    preferences = getattr(user, "preferences", None) or {}
    return (preferences.get("currency") or "USD").upper()
