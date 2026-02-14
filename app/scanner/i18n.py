"""Localization helpers for reports and UI labels."""

from __future__ import annotations

import copy
import re
from typing import Any

from app.i18n_store import get_translation_section

SUPPORTED_LANGS = {"en", "ru"}


def normalize_lang(lang: str | None) -> str:
    """Normalize language code to supported values (`en` or `ru`)."""

    if not lang:
        return "en"
    lowered = lang.lower()
    return lowered if lowered in SUPPORTED_LANGS else "en"


def localize_report(report_payload: dict[str, Any], lang: str) -> dict[str, Any]:
    """Return localized deep copy of report payload."""

    lang = normalize_lang(lang)
    if lang == "en":
        return report_payload

    report_i18n = get_translation_section("report")
    category_name_ru = _dict_str_str(report_i18n.get("category_name_ru"))
    check_name_ru = _dict_str_str(report_i18n.get("check_name_ru"))
    direct_text_ru = _dict_str_str(report_i18n.get("direct_text_ru"))
    patterns_ru = _translation_patterns(report_i18n.get("patterns_ru"))

    localized = copy.deepcopy(report_payload)
    for category in localized.get("categories", []):
        category_id = category.get("id")
        if isinstance(category_id, str) and category_id in category_name_ru:
            category["name"] = category_name_ru[category_id]
        for check in category.get("checks", []):
            check_id = check.get("id")
            if isinstance(check_id, str) and check_id in check_name_ru:
                check["name"] = check_name_ru[check_id]
            check["details"] = _translate_text(str(check.get("details", "")), direct_text_ru, patterns_ru)
            recommendation = check.get("recommendation")
            if recommendation:
                check["recommendation"] = _translate_text(str(recommendation), direct_text_ru, patterns_ru)
        category["recommendations"] = [
            _translate_text(str(item), direct_text_ru, patterns_ru)
            for item in category.get("recommendations", [])
        ]

    comparison = localized.get("comparison")
    if isinstance(comparison, dict):
        for item in comparison.get("checks", []):
            if isinstance(item, dict):
                check_name = item.get("check_name")
                check_id = item.get("check_id")
                if check_name and isinstance(check_id, str):
                    item["check_name"] = check_name_ru.get(check_id, check_name)

    for item in localized.get("fix_plan", []):
        category_id = item.get("category_id")
        if isinstance(category_id, str) and category_id in category_name_ru:
            item["category_name"] = category_name_ru[category_id]
        check_id = item.get("check_id")
        if isinstance(check_id, str) and check_id in check_name_ru:
            item["check_name"] = check_name_ru[check_id]
        item["action"] = _translate_text(str(item.get("action", "")), direct_text_ru, patterns_ru)
    return localized


def get_ui_labels(lang: str) -> dict[str, str]:
    """Return merged UI labels with English fallback."""

    lang = normalize_lang(lang)
    ui = get_translation_section("ui")
    en = _dict_str_str(ui.get("en"))
    cur = _dict_str_str(ui.get(lang))
    merged = dict(en)
    merged.update(cur)
    return merged


def get_client_i18n() -> dict[str, Any]:
    """Return lightweight dictionary used by frontend scripts."""

    client = get_translation_section("client")
    status = _dict_lang_map(client.get("status"))
    text = _dict_lang_map(client.get("text"))
    return {"status": status, "text": text}


def _translate_text(
    text: str,
    direct_text_ru: dict[str, str],
    patterns_ru: list[tuple[re.Pattern[str], str]],
) -> str:
    """Translate text by exact match first, then by regex patterns."""

    if text in direct_text_ru:
        return direct_text_ru[text]
    for pattern, template in patterns_ru:
        match = pattern.match(text)
        if match:
            return template.format(*match.groups())
    return text


def _translation_patterns(raw: Any) -> list[tuple[re.Pattern[str], str]]:
    """Compile translation regex patterns from JSON section."""

    if not isinstance(raw, list):
        return []
    rows: list[tuple[re.Pattern[str], str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        pattern = item.get("pattern")
        template = item.get("template")
        if not isinstance(pattern, str) or not isinstance(template, str):
            continue
        rows.append((re.compile(pattern), template))
    return rows


def _dict_str_str(raw: Any) -> dict[str, str]:
    """Safely cast mapping to `dict[str, str]`."""

    if not isinstance(raw, dict):
        return {}
    result: dict[str, str] = {}
    for key, value in raw.items():
        if isinstance(key, str) and isinstance(value, str):
            result[key] = value
    return result


def _dict_lang_map(raw: Any) -> dict[str, dict[str, str]]:
    """Safely cast nested language mapping."""

    if not isinstance(raw, dict):
        return {}
    result: dict[str, dict[str, str]] = {}
    for lang, mapping in raw.items():
        if not isinstance(lang, str):
            continue
        result[lang] = _dict_str_str(mapping)
    return result
