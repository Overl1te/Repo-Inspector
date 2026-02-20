import httpx

from app.github_client import GitHubClient


def test_pick_line_count_files_includes_dart_files():
    client = GitHubClient()
    tree_paths = [
        "lib/main.dart",
        "lib/src/widget.dart",
        "README.md",
        "src/app.ts",
        ".dart_tool/package_config.json",
    ]
    path_sizes = {path: 1024 for path in tree_paths}

    picked, total = client._pick_line_count_files(tree_paths, path_sizes)

    assert "lib/main.dart" in picked
    assert "lib/src/widget.dart" in picked
    assert "src/app.ts" in picked
    assert total == 3


def test_apply_line_count_fetch_limit():
    paths = ["a.py", "b.py", "c.py"]
    assert GitHubClient._apply_line_count_fetch_limit(paths, None) == paths
    assert GitHubClient._apply_line_count_fetch_limit(paths, 2) == ["a.py", "b.py"]
    assert GitHubClient._apply_line_count_fetch_limit(paths, 0) == []
    assert GitHubClient._apply_line_count_fetch_limit(paths, -5) == []


def test_pick_line_count_files_supports_common_extra_extensions_and_filenames():
    client = GitHubClient()
    tree_paths = [
        "frontend/app.mjs",
        "web/index.html",
        "web/style.css",
        "infra/main.tf",
        "scripts/deploy.sh",
        "Dockerfile",
        "Makefile",
        "notes/readme.txt",
    ]
    path_sizes = {path: 1024 for path in tree_paths}

    picked, total = client._pick_line_count_files(tree_paths, path_sizes)

    assert "frontend/app.mjs" in picked
    assert "web/index.html" in picked
    assert "web/style.css" in picked
    assert "infra/main.tf" in picked
    assert "scripts/deploy.sh" in picked
    assert "Dockerfile" in picked
    assert "Makefile" in picked
    assert "notes/readme.txt" not in picked
    assert total == 7


def test_http_error_detail_for_blank_connect_error():
    detail = GitHubClient._http_error_detail(httpx.ConnectError(""))
    assert detail == "Could not establish network connection to GitHub API."


def test_http_error_detail_prefers_exception_message():
    detail = GitHubClient._http_error_detail(httpx.HTTPError("boom"))
    assert detail == "boom"
