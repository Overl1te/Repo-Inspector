"""Theme configuration storage for SVG cards and generator UI."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

THEME_KEYS = (
    "bg_start",
    "bg_end",
    "border",
    "panel",
    "overlay",
    "chip_bg",
    "chip_text",
    "text",
    "muted",
    "accent",
    "accent_2",
    "accent_soft",
    "track",
    "pass",
    "warn",
    "fail",
)
HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

APP_DIR = Path(__file__).resolve().parent
THEMES_DIR = APP_DIR / "themes"


@dataclass(frozen=True)
class ThemeConfig:
    """One theme entry loaded from `app/themes/*.json`."""

    id: str
    palette: dict[str, str]
    order: int = 100
    is_custom: bool = False


_cache_signature: tuple[tuple[str, int], ...] | None = None
_cache_themes: list[ThemeConfig] | None = None


def load_theme_configs() -> list[ThemeConfig]:
    """Load and cache theme definitions from disk."""

    global _cache_signature, _cache_themes
    files = sorted(THEMES_DIR.glob("*.json"))
    signature = tuple((path.name, path.stat().st_mtime_ns) for path in files)
    if _cache_themes is not None and signature == _cache_signature:
        return _cache_themes

    items: list[ThemeConfig] = []
    for path in files:
        parsed = _parse_theme_file(path)
        if parsed is not None:
            items.append(parsed)

    if not items:
        items = [_fallback_ocean_theme(), _fallback_custom_theme()]
    if not any(item.id == "ocean" for item in items):
        items.append(_fallback_ocean_theme())
    if not any(item.id == "custom" for item in items):
        items.append(_fallback_custom_theme())

    items.sort(key=lambda item: (item.order, item.id))
    _cache_signature = signature
    _cache_themes = items
    return items


def get_theme_palette(theme_id: str) -> dict[str, str]:
    """Return palette map for requested theme with safe fallback."""

    by_id = {item.id: item for item in load_theme_configs()}
    selected = by_id.get(theme_id) or by_id.get("ocean") or _fallback_ocean_theme()
    return dict(selected.palette)


def get_theme_options(ui_labels: Mapping[str, str] | None = None) -> list[dict[str, str | bool]]:
    """Build options payload for UI dropdown."""

    labels = ui_labels or {}
    options: list[dict[str, str | bool]] = []
    for item in load_theme_configs():
        key = f"theme_{item.id}"
        fallback = _humanize_theme_id(item.id)
        options.append(
            {
                "id": item.id,
                "label": labels.get(key, fallback),
                "is_custom": item.is_custom,
            }
        )
    return options


def get_custom_theme_defaults() -> dict[str, str]:
    """Return baseline palette for the custom theme editor."""

    by_id = {item.id: item for item in load_theme_configs()}
    selected = by_id.get("custom") or _fallback_custom_theme()
    return dict(selected.palette)


def _parse_theme_file(path: Path) -> ThemeConfig | None:
    """Parse one theme file and validate required keys."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(payload, dict):
        return None

    raw_id = payload.get("id", path.stem)
    if not isinstance(raw_id, str) or not raw_id.strip():
        return None
    theme_id = raw_id.strip().lower()

    raw_palette = payload.get("palette")
    if not isinstance(raw_palette, dict):
        return None
    palette = _normalize_palette(raw_palette)
    if palette is None:
        return None

    order = _to_int(payload.get("order"), 100)
    is_custom = bool(payload.get("is_custom", False))
    return ThemeConfig(id=theme_id, palette=palette, order=order, is_custom=is_custom)


def _normalize_palette(raw_palette: dict[object, object]) -> dict[str, str] | None:
    """Normalize and validate palette hex colors."""

    normalized: dict[str, str] = {}
    for key in THEME_KEYS:
        raw = raw_palette.get(key)
        if not isinstance(raw, str):
            return None
        color = _normalize_hex(raw)
        if color is None:
            return None
        normalized[key] = color
    return normalized


def _normalize_hex(value: str) -> str | None:
    """Normalize short hex to full uppercase form."""

    candidate = value.strip()
    if not HEX_COLOR_RE.match(candidate):
        return None
    if len(candidate) == 4:
        candidate = "#" + "".join(ch * 2 for ch in candidate[1:])
    return candidate.upper()


def _to_int(value: object, default: int) -> int:
    """Parse integer with fallback to default."""

    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _humanize_theme_id(theme_id: str) -> str:
    """Convert `theme_id` to human-readable label."""

    text = theme_id.strip().replace("_", " ").replace("-", " ")
    if not text:
        return "Theme"
    return " ".join(part.capitalize() for part in text.split())


def _fallback_ocean_theme() -> ThemeConfig:
    """Built-in fallback when theme files are unavailable."""

    return ThemeConfig(
        id="ocean",
        order=10,
        palette={
            "bg_start": "#F8FBFF",
            "bg_end": "#EEF5FF",
            "border": "#A8CBFF",
            "panel": "#FFFFFF",
            "overlay": "#EDF4FF",
            "chip_bg": "#E7F0FF",
            "chip_text": "#2D4E83",
            "text": "#14284B",
            "muted": "#3F6191",
            "accent": "#16A4E0",
            "accent_2": "#1AB9A2",
            "accent_soft": "#B8DBFF",
            "track": "#D3E3FB",
            "pass": "#0F7F39",
            "warn": "#B55A0C",
            "fail": "#BE1D2D",
        },
    )


def _fallback_custom_theme() -> ThemeConfig:
    """Built-in fallback for custom theme defaults."""

    ocean = _fallback_ocean_theme()
    return ThemeConfig(
        id="custom",
        order=999,
        is_custom=True,
        palette=dict(ocean.palette),
    )
