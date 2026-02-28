"""Regression tests for HEAD support on stats API endpoints."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_readme_stats_api_head_svg_returns_image_headers_without_body() -> None:
    response = client.head("/api?owner=octocat&repo=Hello-World&kind=repo&format=svg&cache_seconds=21600")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert response.headers["cache-control"] == "public, max-age=21600"
    assert response.content == b""


def test_readme_stats_api_head_json_returns_json_headers_without_body() -> None:
    response = client.head("/api?owner=octocat&repo=Hello-World&kind=quality&format=json")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.content == b""


def test_repo_stats_svg_head_returns_image_headers_without_body() -> None:
    response = client.head("/api/stats/repo/octocat/Hello-World.svg?cache_seconds=21600")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert response.headers["cache-control"] == "public, max-age=21600"
    assert response.content == b""


def test_quality_stats_svg_head_returns_image_headers_without_body() -> None:
    response = client.head("/api/stats/quality/octocat/Hello-World.svg?cache_seconds=300")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert response.headers["cache-control"] == "public, max-age=300"
    assert response.content == b""


def test_legacy_stats_svg_head_returns_image_headers_without_body() -> None:
    response = client.head("/api/stats/octocat/Hello-World.svg?cache_seconds=21600")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert response.headers["cache-control"] == "public, max-age=21600"
    assert response.content == b""
