# ruff: noqa: E501
"""SVG card rendering for repository and quality stats endpoints."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from app.i18n_store import get_translation_section
from app.theme_store import HEX_COLOR_RE, THEME_KEYS, get_theme_palette

APP_DIR = Path(__file__).resolve().parent
SVG_TEMPLATE_DIR = APP_DIR / "templates" / "svg"
SVG_TEMPLATE_ENV = Environment(
    loader=FileSystemLoader(str(SVG_TEMPLATE_DIR)),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)

def build_repo_stats_svg(
    payload: dict[str, Any],
    *,
    theme: str = "ocean",
    custom_theme: dict[str, str] | None = None,
    locale: str = "en",
    card_width: int = 760,
    langs_count: int = 4,
    hide: set[str] | None = None,
    title: str | None = None,
    animate: bool = False,
    animation: str = "all",
    duration_ms: int = 1400,
) -> str:
    """Render repository metadata card as SVG."""

    palette = _theme(theme, overrides=custom_theme)
    labels = _labels(locale)
    repository = payload.get("repository", {})
    if not isinstance(repository, dict):
        repository = {}

    hide_set = _normalize_flags(hide)
    anim_flags = _animation_flags(animate, animation, supports_ring=False)
    card_width = _clamp_int(card_width, 640, 1400)

    owner = str(repository.get("owner", ""))
    name = str(repository.get("name", ""))
    full_name = f"{owner}/{name}".strip("/") or "unknown/repository"
    title_text = _clip(title.strip(), 58) if title and title.strip() else full_name
    description = str(repository.get("description") or labels["no_description"])
    description = _clip(description, 96)
    na_label = labels["na"]
    pushed_at = str(repository.get("pushed_at") or na_label)
    pushed_at = pushed_at.split("T", 1)[0] if "T" in pushed_at else pushed_at
    default_branch = str(repository.get("default_branch") or na_label)
    license_name = str(repository.get("license_name") or na_label)
    size_kb = _compact_int(repository.get("size_kb", 0))
    has_releases = bool(repository.get("has_releases"))
    has_tags = bool(repository.get("has_tags"))

    show_description = "description" not in hide_set
    show_languages = "languages" not in hide_set
    show_footer = "footer" not in hide_set
    show_meta = "meta" not in hide_set

    stat_items = [
        ("stars", labels["stars"], _compact_int(repository.get("stars", 0))),
        ("forks", labels["forks"], _compact_int(repository.get("forks", 0))),
        ("issues", labels["issues"], _compact_int(repository.get("open_issues", 0))),
        ("watchers", labels["watchers"], _compact_int(repository.get("watchers", 0))),
    ]
    stat_items = [item for item in stat_items if item[0] not in hide_set]
    if not stat_items:
        stat_items = [("stars", labels["stars"], "0")]

    top_languages = _top_languages(repository.get("languages"), limit=max(1, langs_count))
    card_height = 290 if show_languages else 236
    if not show_footer:
        card_height -= 18

    base_x = 28
    metric_y = 112 if (show_description or show_meta) else 90
    metric_gap = 12
    metric_w = max(94, (card_width - base_x * 2 - metric_gap * (len(stat_items) - 1)) // len(stat_items))
    bars_y = metric_y + 78
    bars_w = card_width - base_x * 2
    footer_y = card_height - 14

    metric_svg: list[str] = []
    for idx, (_, label, value) in enumerate(stat_items):
        x = base_x + idx * (metric_w + metric_gap)
        delay = 120 + idx * 75
        cls = "stat-cell animate-rise" if anim_flags["soft"] else "stat-cell"
        metric_svg.append(
            f"""
    <g class="{cls}" style="--d:{delay}ms;">
      <rect x="{x}" y="{metric_y}" width="{metric_w}" height="54" rx="12" fill="{palette["panel"]}" />
      <rect x="{x + 1}" y="{metric_y}" width="{metric_w - 2}" height="4" rx="2" fill="{palette["accent_soft"]}" />
      <text x="{x + 12}" y="{metric_y + 22}" class="meta">{escape(label)}</text>
      <text x="{x + 12}" y="{metric_y + 44}" class="metric-value">{escape(value)}</text>
    </g>
"""
        )

    meta_line = ""
    if show_meta:
        meta_items = [
            f'{labels["branch"]}: {escape(default_branch)}',
            f'{labels["license"]}: {escape(license_name)}',
            f'{labels["size"]}: {escape(size_kb)} KB',
            f'{labels["releases"]}: {labels["yes"] if has_releases else labels["no"]}',
            f'{labels["tags"]}: {labels["yes"] if has_tags else labels["no"]}',
        ]
        meta_chunks: list[str] = []
        cursor = base_x
        for idx, item in enumerate(meta_items[:5]):
            width = min(180, max(96, len(item) * 6 + 22))
            meta_chunks.append(
                f'<g class="animate-rise" style="--d:{90 + idx * 50}ms;"><rect x="{cursor}" y="70" width="{width}" height="28" rx="14" fill="{palette["chip_bg"]}" />'
                f'<text x="{cursor + 10}" y="88" class="chip-text">{item}</text></g>'
            )
            cursor += width + 8
            if cursor > card_width - 120:
                break
        meta_line = "".join(meta_chunks)

    languages_svg = ""
    if show_languages:
        bars = _language_bars(
            top_languages,
            x=base_x,
            y=bars_y,
            width=bars_w,
            height=12,
            animated=anim_flags["bars"],
        )
        legend = _language_legend(
            top_languages,
            x=base_x,
            y=bars_y + 36,
            color=palette["text"],
            empty_label=labels["no_language_data"],
        )
        languages_svg = f"""
  <text x="{base_x}" y="{bars_y - 8}" class="meta">{labels["languages"]}</text>
  {bars}
  {legend}
"""

    description_line = (
        f'<text x="{base_x}" y="58" class="subtitle">{escape(description)}</text>' if show_description else ""
    )
    footer_line = (
        f'<text x="{base_x}" y="{footer_y}" class="meta">{labels["last_push"]}: {escape(pushed_at)}</text>'
        if show_footer
        else ""
    )

    style = _style_block(palette, anim_flags, duration_ms)
    return _render_svg_template(
        "repo_card.xml",
        card_width=card_width,
        card_height=card_height,
        border=palette["border"],
        bg_start=palette["bg_start"],
        bg_end=palette["bg_end"],
        base_x=base_x,
        repo_card_aria=labels["repo_card_aria"],
        title_text=escape(title_text),
        description_line=description_line,
        meta_line=meta_line,
        metric_svg="".join(metric_svg),
        languages_svg=languages_svg,
        footer_line=footer_line,
        style_block=style,
    )


def build_quality_stats_svg(
    payload: dict[str, Any],
    *,
    theme: str = "ocean",
    custom_theme: dict[str, str] | None = None,
    locale: str = "en",
    card_width: int = 760,
    hide: set[str] | None = None,
    title: str | None = None,
    animate: bool = False,
    animation: str = "all",
    duration_ms: int = 1400,
) -> str:
    """Render quality snapshot card as SVG."""

    palette = _theme(theme, overrides=custom_theme)
    labels = _labels(locale)
    hide_set = _normalize_flags(hide)
    anim_flags = _animation_flags(animate, animation, supports_ring=True)
    card_width = _clamp_int(card_width, 640, 1400)

    repository = payload.get("repository", {})
    quality = payload.get("quality", {})
    if not isinstance(repository, dict):
        repository = {}
    if not isinstance(quality, dict):
        quality = {}

    owner = str(repository.get("owner", ""))
    name = str(repository.get("name", ""))
    full_name = f"{owner}/{name}".strip("/") or "unknown/repository"
    title_text = _clip(title.strip(), 58) if title and title.strip() else full_name

    score = _clamp_int(int(quality.get("score_total", 0) or 0), 0, 100)
    ring_total = 251.2
    ring_value = round((score / 100) * ring_total, 2)
    ring_offset = max(0.0, round(ring_total - ring_value, 2))
    ring_seconds = max(0.4, min(6.5, duration_ms / 1000))

    code_lines = _compact_int(quality.get("total_code_lines", 0))
    code_files = _compact_int(quality.get("total_code_files", 0))
    scanned_files = _compact_int(quality.get("scanned_code_files", 0))
    na_label = labels["na"]
    commit_sha = str(quality.get("commit_sha") or na_label)
    commit_short = commit_sha[:7] if commit_sha != na_label else na_label
    finished_at = str(quality.get("finished_at") or na_label)
    finished_short = finished_at.split("T", 1)[0] if "T" in finished_at else finished_at

    status_counts = quality.get("status_counts")
    if not isinstance(status_counts, dict):
        status_counts = {}
    pass_count = int(status_counts.get("pass", 0) or 0)
    warn_count = int(status_counts.get("warn", 0) or 0)
    fail_count = int(status_counts.get("fail", 0) or 0)

    categories = quality.get("category_scores")
    if not isinstance(categories, list):
        categories = []
    category_rows = _category_rows(categories, limit=3)

    stacks = quality.get("detected_stacks")
    if not isinstance(stacks, list):
        stacks = []
    stacks_text = ", ".join(str(item) for item in stacks[:4]) if stacks else na_label

    show_status = "status" not in hide_set
    show_lines = "lines" not in hide_set
    show_commit = "commit" not in hide_set
    show_stacks = "stacks" not in hide_set
    show_footer = "footer" not in hide_set
    show_ring = "ring" not in hide_set
    show_categories = "categories" not in hide_set

    detail_pairs = _detail_pairs(
        show_lines=show_lines,
        show_stacks=show_stacks,
        show_commit=show_commit,
        show_footer=show_footer,
        labels=labels,
        code_lines=code_lines,
        code_files=code_files,
        scanned_files=scanned_files,
        stacks_text=stacks_text,
        commit_short=commit_short,
        finished_short=finished_short,
    )

    ring_panel_w = 228 if show_ring else 0
    left_w = card_width - 60 - ring_panel_w - (18 if show_ring else 0)
    ring_x = card_width - 30 - ring_panel_w
    left_x = 30
    left_y = 76

    status_h = 66 if show_status else 0
    details_rows = (len(detail_pairs) + 1) // 2
    details_h = details_rows * 42 if details_rows else 0
    categories_h = (28 + len(category_rows) * 24) if (show_categories and category_rows) else 0
    left_h = 18 + status_h + details_h + categories_h + 16
    card_height = max(292, left_y + left_h + 18)
    ring_panel_h = card_height - 48
    ring_center_y = int(ring_panel_h / 2) + 2

    status_svg = ""
    if show_status:
        status_w = max(74, int((left_w - 32) / 3))
        status_gap = 10
        s1 = left_x + 10
        s2 = s1 + status_w + status_gap
        s3 = s2 + status_w + status_gap
        cls = "status-cell animate-rise" if anim_flags["soft"] else "status-cell"
        status_svg = f"""
    <g class="{cls}" style="--d:120ms;">
      <rect x="{s1}" y="94" width="{status_w}" height="52" rx="12" fill="{palette["panel"]}" />
      <text x="{s1 + 12}" y="114" class="meta">{labels["pass"]}</text>
      <text x="{s1 + 12}" y="139" class="status-pass">{pass_count}</text>
    </g>
    <g class="{cls}" style="--d:185ms;">
      <rect x="{s2}" y="94" width="{status_w}" height="52" rx="12" fill="{palette["panel"]}" />
      <text x="{s2 + 12}" y="114" class="meta">{labels["warn"]}</text>
      <text x="{s2 + 12}" y="139" class="status-warn">{warn_count}</text>
    </g>
    <g class="{cls}" style="--d:250ms;">
      <rect x="{s3}" y="94" width="{status_w}" height="52" rx="12" fill="{palette["panel"]}" />
      <text x="{s3 + 12}" y="114" class="meta">{labels["fail"]}</text>
      <text x="{s3 + 12}" y="139" class="status-fail">{fail_count}</text>
    </g>
"""

    details_start = 170 if show_status else 98
    detail_svg: list[str] = []
    detail_w = max(100, int((left_w - 30) / 2))
    detail_gap = 10
    for idx, pair in enumerate(detail_pairs):
        row = idx // 2
        col = idx % 2
        x = left_x + 10 + col * (detail_w + detail_gap)
        y = details_start + row * 42
        cls = "meta-line animate-rise" if anim_flags["soft"] else "meta-line"
        detail_svg.append(
            f'<g class="{cls}" style="--d:{145 + idx * 35}ms;">'
            f'<text x="{x}" y="{y}" class="meta">{escape(pair[0])}</text>'
            f'<text x="{x}" y="{y + 18}" class="detail-value">{escape(pair[1])}</text>'
            f"</g>"
        )

    category_svg = ""
    if show_categories and category_rows:
        cat_title_y = details_start + details_rows * 42 + 16
        bars: list[str] = [
            f'<text x="{left_x + 10}" y="{cat_title_y}" class="meta">{labels["categories"]}</text>'
        ]
        y = cat_title_y + 18
        track_w = max(left_w - 174, 96)
        for idx, row in enumerate(category_rows):
            delay = 190 + idx * 55
            width = int(row["ratio"] * track_w)
            bar_class = "cat-bar lang-seg" if anim_flags["bars"] else "cat-bar"
            bars.append(
                f'<text x="{left_x + 10}" y="{y + 3}" class="meta">{escape(str(row["name"]))}</text>'
                f'<rect x="{left_x + 112}" y="{y - 7}" width="{track_w}" height="10" rx="5" fill="{palette["track"]}" />'
                f'<rect x="{left_x + 112}" y="{y - 7}" width="{max(width, 6)}" height="10" rx="5" fill="{palette["accent"]}" class="{bar_class}" style="--d:{delay}ms;" />'
                f'<text x="{left_x + 112 + track_w + 8}" y="{y + 3}" class="meta">{row["score"]}/{row["weight"]}</text>'
            )
            y += 24
        category_svg = "".join(bars)

    ring_svg = ""
    if show_ring:
        ring_class = "ring-progress animate-ring" if anim_flags["ring"] else "ring-progress"
        ring_dasharray = f"{ring_total}"
        dashoffset = ring_offset
        animate_tag = ""
        if anim_flags["ring"]:
            animate_tag = (
                f'<animate attributeName="stroke-dashoffset" from="{ring_total}" to="{ring_offset}" '
                f'dur="{ring_seconds}s" calcMode="spline" keySplines="0.22 1 0.36 1" fill="freeze" />'
            )
        ring_svg = f"""
  <g transform="translate({ring_x},24)">
    <rect x="0" y="0" width="{ring_panel_w}" height="{ring_panel_h}" rx="16" fill="{palette["panel"]}" />
    <text x="{ring_panel_w // 2}" y="34" text-anchor="middle" class="meta">{labels["quality_score"]}</text>
    <g transform="translate({ring_panel_w // 2},{ring_center_y})">
      <circle cx="0" cy="0" r="40" fill="none" stroke="{palette["track"]}" stroke-width="10" />
      <circle cx="0" cy="0" r="40" fill="none" stroke="url(#ring-grad)" stroke-width="10" stroke-linecap="round"
        stroke-dasharray="{ring_dasharray}" stroke-dashoffset="{dashoffset}" transform="rotate(-90)" class="{ring_class}">{animate_tag}</circle>
      <text x="0" y="8" text-anchor="middle" class="ring-score">{score}</text>
      <text x="0" y="28" text-anchor="middle" class="meta">/100</text>
    </g>
    <text x="{ring_panel_w // 2}" y="{ring_panel_h - 20}" text-anchor="middle" class="subtitle">{labels["quality_subtitle"]}</text>
  </g>
"""

    style = _style_block(palette, anim_flags, duration_ms)
    return _render_svg_template(
        "quality_card.xml",
        card_width=card_width,
        card_height=card_height,
        border=palette["border"],
        bg_start=palette["bg_start"],
        bg_end=palette["bg_end"],
        accent=palette["accent"],
        accent_2=palette["accent_2"],
        overlay=palette["overlay"],
        left_w=left_w,
        left_h=left_h,
        left_x=left_x,
        left_y=left_y,
        quality_card_aria=labels["quality_card_aria"],
        title_text=escape(title_text),
        quality_subtitle=labels["quality_subtitle"],
        status_svg=status_svg,
        detail_svg="".join(detail_svg),
        category_svg=category_svg,
        ring_svg=ring_svg,
        style_block=style,
    )


def _style_block(palette: dict[str, str], anim_flags: dict[str, bool], duration_ms: int) -> str:
    """Return CSS block injected into SVG template."""

    duration_ms = _clamp_int(duration_ms, 350, 7000)
    rise_ms = int(duration_ms * 0.55)
    bar_ms = int(duration_ms * 0.7)
    ring_ms = int(duration_ms * 0.9)

    animations = ""
    if anim_flags["soft"]:
        animations += f"""
    .animate-rise {{
      opacity: 0;
      transform: translateY(8px);
      animation: rise {rise_ms}ms cubic-bezier(0.22, 1, 0.36, 1) forwards;
      animation-delay: var(--d, 0ms);
    }}
"""
    if anim_flags["bars"]:
        animations += f"""
    .lang-seg {{
      transform-origin: left center;
      transform-box: fill-box;
      transform: scaleX(0.001);
      animation: grow {bar_ms}ms cubic-bezier(0.22, 1, 0.36, 1) forwards;
      animation-delay: var(--d, 0ms);
    }}
"""
    if anim_flags["ring"]:
        animations += f"""
    .animate-ring {{
      animation: ring {ring_ms}ms cubic-bezier(0.22, 1, 0.36, 1) forwards;
    }}
"""

    return f"""
  <style>
    .title {{
      fill: {palette["text"]};
      font-size: 24px;
      font-weight: 760;
      font-family: 'Sora', Arial, sans-serif;
      letter-spacing: -0.012em;
    }}
    .subtitle {{
      fill: {palette["muted"]};
      font-size: 12px;
      font-family: 'Sora', Arial, sans-serif;
      font-weight: 560;
    }}
    .meta, .meta-line {{
      fill: {palette["muted"]};
      font-size: 11.2px;
      font-family: 'Sora', Arial, sans-serif;
      font-weight: 560;
    }}
    .chip-text {{
      fill: {palette["chip_text"]};
      font-size: 12.2px;
      font-family: 'Sora', Arial, sans-serif;
      font-weight: 600;
    }}
    .metric-value {{
      fill: {palette["text"]};
      font-size: 21px;
      font-family: 'Sora', Arial, sans-serif;
      font-weight: 780;
    }}
    .ring-score {{
      fill: {palette["text"]};
      font-size: 33px;
      font-family: 'Sora', Arial, sans-serif;
      font-weight: 760;
    }}
    .status-pass {{
      fill: {palette["pass"]};
      font-size: 25px;
      font-weight: 740;
      font-family: 'Sora', Arial, sans-serif;
    }}
    .status-warn {{
      fill: {palette["warn"]};
      font-size: 25px;
      font-weight: 740;
      font-family: 'Sora', Arial, sans-serif;
    }}
    .status-fail {{
      fill: {palette["fail"]};
      font-size: 25px;
      font-weight: 740;
      font-family: 'Sora', Arial, sans-serif;
    }}
    .detail-value {{
      fill: {palette["text"]};
      font-size: 16px;
      font-weight: 640;
      font-family: 'Sora', Arial, sans-serif;
    }}
    {animations}
    @keyframes rise {{
      from {{ opacity: 0; transform: translateY(8px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes grow {{
      from {{ transform: scaleX(0.001); }}
      to {{ transform: scaleX(1); }}
    }}
    @keyframes ring {{ from {{ opacity: 1; }} to {{ opacity: 1; }} }}
  </style>
"""


def _category_rows(raw: list[object], limit: int = 4) -> list[dict[str, object]]:
    """Convert category list into compact progress-bar rows."""

    rows: list[dict[str, object]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if not isinstance(name, str):
            continue
        score = _to_int(item.get("score"))
        weight = max(_to_int(item.get("weight")), 1)
        ratio = max(0.0, min(1.0, score / weight))
        rows.append({"name": name, "score": score, "weight": weight, "ratio": ratio})
    return rows[:limit]


def _detail_pairs(
    *,
    show_lines: bool,
    show_stacks: bool,
    show_commit: bool,
    show_footer: bool,
    labels: dict[str, str],
    code_lines: str,
    code_files: str,
    scanned_files: str,
    stacks_text: str,
    commit_short: str,
    finished_short: str,
) -> list[tuple[str, str]]:
    """Build key-value lines shown in the quality details area."""

    rows: list[tuple[str, str]] = []
    if show_lines:
        rows.extend(
            [
                (labels["code_lines"], code_lines),
                (labels["code_files"], code_files),
                (labels["scanned"], scanned_files),
            ]
        )
    if show_stacks:
        rows.append((labels["stacks"], stacks_text))
    if show_commit:
        rows.append((labels["commit"], commit_short))
    if show_footer:
        rows.append((labels["updated"], finished_short))
    return rows[:8]


def _animation_flags(animate: bool, animation: str, *, supports_ring: bool) -> dict[str, bool]:
    """Resolve animation toggles for template sections."""

    if not animate:
        return {"soft": False, "bars": False, "ring": False}
    mode = (animation or "all").strip().lower()
    if mode in {"none", "off"}:
        return {"soft": False, "bars": False, "ring": False}
    if mode == "soft":
        return {"soft": True, "bars": False, "ring": False}
    if mode == "bars":
        return {"soft": False, "bars": True, "ring": False}
    if mode == "ring":
        return {"soft": False, "bars": False, "ring": supports_ring}
    return {"soft": True, "bars": True, "ring": supports_ring}


def _normalize_flags(value: set[str] | None) -> set[str]:
    """Normalize hide flags to lowercase set."""

    if not value:
        return set()
    return {item.strip().lower() for item in value if item and item.strip()}


def _theme(name: str, overrides: dict[str, str] | None = None) -> dict[str, str]:
    """Resolve theme palette and apply validated custom overrides."""

    palette = get_theme_palette(name)
    for key, value in _sanitize_theme_overrides(overrides).items():
        if key in palette:
            palette[key] = value
    return palette


def _sanitize_theme_overrides(overrides: dict[str, str] | None) -> dict[str, str]:
    """Keep only valid custom color keys."""

    if not overrides:
        return {}
    sanitized: dict[str, str] = {}
    for key in THEME_KEYS:
        raw = overrides.get(key)
        if not isinstance(raw, str):
            continue
        color = _normalize_hex_color(raw)
        if color:
            sanitized[key] = color
    return sanitized


def _normalize_hex_color(value: str) -> str | None:
    """Validate and normalize hex color string."""

    raw = value.strip()
    if not HEX_COLOR_RE.match(raw):
        return None
    if len(raw) == 4:
        raw = "#" + "".join(ch * 2 for ch in raw[1:])
    return raw.upper()


def _labels(locale: str) -> dict[str, str]:
    """Return localized labels for SVG cards."""

    defaults = {
        "repo_card_aria": "Repository stats card",
        "quality_card_aria": "Quality score card",
        "no_description": "No description",
        "stars": "Stars",
        "forks": "Forks",
        "issues": "Issues",
        "watchers": "Watchers",
        "languages": "Languages",
        "last_push": "Last push",
        "branch": "Branch",
        "license": "License",
        "size": "Size",
        "releases": "Releases",
        "tags": "Tags",
        "yes": "yes",
        "no": "no",
        "na": "n/a",
        "no_language_data": "No language data",
        "quality_score": "Quality score",
        "quality_subtitle": "Current quality snapshot",
        "pass": "PASS",
        "warn": "WARN",
        "fail": "FAIL",
        "code_lines": "Code lines",
        "code_files": "Code files",
        "scanned": "Scanned",
        "stacks": "Stacks",
        "commit": "Commit",
        "updated": "Updated",
        "categories": "Categories",
    }
    stats_i18n = get_translation_section("stats_card")
    lang = "ru" if locale.lower() == "ru" else "en"
    raw = stats_i18n.get(lang)
    if not isinstance(raw, dict):
        return defaults
    translated = {key: value for key, value in raw.items() if isinstance(key, str) and isinstance(value, str)}
    merged = dict(defaults)
    merged.update(translated)
    return merged


def _clip(value: str, max_len: int) -> str:
    """Clip long text and append ellipsis."""

    if len(value) <= max_len:
        return value
    return value[: max_len - 1].rstrip() + "..."


def _compact_int(value: object) -> str:
    """Format integer in compact `K/M` style."""

    number = _to_int(value)
    abs_number = abs(number)
    if abs_number >= 1_000_000:
        return f"{number / 1_000_000:.1f}M".replace(".0M", "M")
    if abs_number >= 1_000:
        return f"{number / 1_000:.1f}K".replace(".0K", "K")
    return str(number)


def _top_languages(raw: object, limit: int = 4) -> list[tuple[str, int]]:
    """Return sorted top languages with line/byte totals."""

    rows: list[tuple[str, int]] = []
    if isinstance(raw, dict):
        for key, value in raw.items():
            if not isinstance(key, str):
                continue
            amount = _to_int(value)
            if amount > 0:
                rows.append((key, amount))
    elif isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            if not isinstance(name, str):
                continue
            amount = _to_int(item.get("bytes"))
            if amount > 0:
                rows.append((name, amount))
    rows.sort(key=lambda item: item[1], reverse=True)
    return rows[:limit]


def _language_bars(
    languages: list[tuple[str, int]],
    *,
    x: int,
    y: int,
    width: int,
    height: int,
    animated: bool,
) -> str:
    """Render stacked language percentage bar."""

    if not languages:
        return (
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="6" fill="#dbeafe" />'
            f'<rect x="{x}" y="{y}" width="{max(int(width * 0.28), 24)}" height="{height}" rx="6" fill="#0ea5e9" />'
        )

    total = sum(item[1] for item in languages)
    chunks = [f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="6" fill="#dbeafe" />']
    cursor = x
    for idx, (_, amount) in enumerate(languages):
        part_width = width - (cursor - x) if idx == len(languages) - 1 else max(int(width * (amount / max(total, 1))), 14)
        cls = "lang-seg" if animated else ""
        delay = 120 + idx * 90
        chunks.append(
            f'<rect x="{cursor}" y="{y}" width="{part_width}" height="{height}" rx="6" fill="{_bar_color(idx)}" class="{cls}" style="--d:{delay}ms;" />'
        )
        cursor += part_width
    return "".join(chunks)


def _language_legend(
    languages: list[tuple[str, int]],
    *,
    x: int,
    y: int,
    color: str,
    empty_label: str = "No language data",
) -> str:
    """Render language legend with color markers."""

    if not languages:
        return (
            f'<text x="{x}" y="{y}" fill="{color}" font-size="11" '
            f'font-family="\'Sora\',Arial,sans-serif">{escape(empty_label)}</text>'
        )
    total = sum(item[1] for item in languages)
    parts: list[str] = []
    cursor = x
    for idx, (name, amount) in enumerate(languages):
        percent = round((amount / max(total, 1)) * 100)
        label = f"{escape(name)} {percent}%"
        dot_color = _bar_color(idx)
        dot_cx = cursor + 5
        parts.append(
            f'<circle cx="{dot_cx}" cy="{y - 4}" r="4.5" fill="{dot_color}" />'
            f'<text x="{cursor + 14}" y="{y}" fill="{color}" font-size="11" font-family="\'Sora\',Arial,sans-serif">{label}</text>'
        )
        cursor += min(214, max(108, len(name) * 7 + 44))
    return "".join(parts)


def _bar_color(index: int) -> str:
    """Return deterministic color for language segment index."""

    palette = ["#0ea5e9", "#22c55e", "#f59e0b", "#a855f7", "#ec4899", "#6366f1", "#14b8a6"]
    return palette[index % len(palette)]


def _clamp_int(value: int, minimum: int, maximum: int) -> int:
    """Clamp integer into inclusive range."""

    return max(minimum, min(maximum, value))


def _to_int(value: object) -> int:
    """Best-effort integer conversion."""

    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def _render_svg_template(template_name: str, **context: object) -> str:
    """Render XML template with provided context values."""

    return SVG_TEMPLATE_ENV.get_template(template_name).render(**context)

