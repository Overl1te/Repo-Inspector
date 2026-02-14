from app.stats_card import build_quality_stats_svg, build_repo_stats_svg


def _payload() -> dict[str, object]:
    return {
        "repository": {
            "owner": "octocat",
            "name": "hello-world",
            "description": "Demo repository for card rendering",
            "stars": 1200,
            "forks": 210,
            "open_issues": 9,
            "watchers": 57,
            "pushed_at": "2026-02-10T12:00:00+00:00",
            "languages": [
                {"name": "Python", "bytes": 6000},
                {"name": "TypeScript", "bytes": 3000},
                {"name": "Shell", "bytes": 1000},
            ],
        },
        "quality": {
            "score_total": 78,
            "total_code_lines": 8450,
            "total_code_files": 120,
        },
    }


def test_build_repo_stats_svg_contains_core_fields() -> None:
    svg = build_repo_stats_svg(_payload(), theme="ocean")
    assert "octocat/hello-world" in svg
    assert "Stars" in svg
    assert "Python" in svg


def test_build_repo_stats_svg_renders_languages() -> None:
    svg = build_repo_stats_svg(_payload(), theme="light")
    assert "Python" in svg
    assert "TypeScript" in svg
    assert "Shell" in svg


def test_build_repo_stats_svg_handles_missing_languages() -> None:
    payload = _payload()
    repository = payload.get("repository")
    assert isinstance(repository, dict)
    repository["languages"] = []
    svg = build_repo_stats_svg(payload, theme="midnight")
    assert "No language data" in svg


def test_build_repo_stats_svg_hides_sections() -> None:
    svg = build_repo_stats_svg(
        _payload(),
        hide={"description", "languages", "watchers"},
        title="Custom title",
    )
    assert "Custom title" in svg
    assert "Languages" not in svg


def test_build_quality_stats_svg_contains_score_and_counts() -> None:
    svg = build_quality_stats_svg(_payload(), theme="ocean")
    assert "Quality score" in svg
    assert ">78<" in svg
    assert "PASS" in svg


def test_build_quality_stats_svg_locale_ru() -> None:
    svg = build_quality_stats_svg(_payload(), locale="ru", hide={"footer"})
    assert "Итоговая оценка" in svg


def test_repo_svg_animation_enabled() -> None:
    svg = build_repo_stats_svg(_payload(), animate=True, animation="bars", duration_ms=1800)
    assert "lang-seg" in svg
    assert "animation: grow" in svg


def test_quality_svg_ring_animation_enabled() -> None:
    svg = build_quality_stats_svg(_payload(), animate=True, animation="ring")
    assert "animate-ring" in svg
    assert "animation: ring" in svg


def test_custom_theme_overrides_are_applied() -> None:
    svg = build_quality_stats_svg(
        _payload(),
        theme="custom",
        custom_theme={"accent": "#123abc", "text": "#222244"},
    )
    assert "#123ABC" in svg
    assert "#222244" in svg


def test_invalid_custom_theme_override_is_ignored() -> None:
    svg = build_repo_stats_svg(_payload(), theme="custom", custom_theme={"text": "not-a-color"})
    assert "not-a-color" not in svg
    assert "#14284B" in svg


def test_short_hex_custom_theme_override_is_expanded() -> None:
    svg = build_quality_stats_svg(_payload(), theme="custom", custom_theme={"warn": "#abc"})
    assert "#AABBCC" in svg

