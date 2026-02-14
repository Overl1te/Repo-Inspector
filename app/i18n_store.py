"""Translation catalog loader used by server and templates."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

APP_DIR = Path(__file__).resolve().parent
TRANSLATIONS_PATH = APP_DIR / "locales" / "translations.json"


@lru_cache
def load_translations() -> dict[str, Any]:
    """Read translations JSON and return validated mapping."""

    # `utf-8-sig` supports both UTF-8 with and without BOM.
    # This avoids mojibake in Windows editors that may re-save with BOM.
    with TRANSLATIONS_PATH.open("r", encoding="utf-8-sig") as fp:
        payload = json.load(fp)
    if not isinstance(payload, dict):
        raise ValueError("translations.json root must be an object")
    return payload


def get_translation_section(section: str) -> dict[str, Any]:
    """Return one top-level section or an empty dictionary."""

    payload = load_translations()
    raw = payload.get(section)
    return raw if isinstance(raw, dict) else {}
