"""Async GitHub REST API client used by scan jobs."""

import asyncio
import base64
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

from app.config import get_settings


class GitHubAPIError(Exception):
    """Raised when GitHub API request fails or returns invalid response."""

    pass


@dataclass
class RepoSnapshot:
    """Repository data required by quality checks."""

    owner: str
    name: str
    url: str
    default_branch: str
    default_branch_sha: str | None
    updated_at: datetime | None
    pushed_at: datetime | None
    tree_paths: list[str]
    file_contents: dict[str, str]
    has_license: bool
    has_release_or_tag: bool
    workflow_paths: list[str]
    line_count_paths: list[str]
    line_count_candidates_total: int
    line_count_sampled: bool


@dataclass
class RepoPublicStats:
    """Public metadata used to render stats endpoints/cards."""

    owner: str
    name: str
    full_name: str
    html_url: str
    description: str | None
    stars: int
    forks: int
    open_issues: int
    watchers: int
    default_branch: str
    primary_language: str | None
    license_name: str | None
    topics: list[str]
    archived: bool
    is_fork: bool
    size_kb: int
    created_at: datetime | None
    updated_at: datetime | None
    pushed_at: datetime | None
    homepage: str | None
    has_releases: bool
    has_tags: bool
    languages: dict[str, int]


class GitHubClient:
    """High-level GitHub API client with typed helper methods."""

    LINE_COUNT_EXTENSIONS = {
        ".py",
        ".js",
        ".mjs",
        ".cjs",
        ".jsx",
        ".ts",
        ".mts",
        ".cts",
        ".tsx",
        ".html",
        ".htm",
        ".css",
        ".scss",
        ".sass",
        ".less",
        ".java",
        ".kt",
        ".kts",
        ".dart",
        ".cs",
        ".cpp",
        ".cc",
        ".cxx",
        ".c",
        ".h",
        ".hpp",
        ".m",
        ".mm",
        ".go",
        ".rs",
        ".php",
        ".rb",
        ".swift",
        ".scala",
        ".groovy",
        ".gradle",
        ".fs",
        ".fsi",
        ".fsx",
        ".vb",
        ".vbs",
        ".r",
        ".rmd",
        ".jl",
        ".lua",
        ".ex",
        ".exs",
        ".erl",
        ".hrl",
        ".clj",
        ".cljs",
        ".cljc",
        ".hs",
        ".elm",
        ".ml",
        ".mli",
        ".pl",
        ".pm",
        ".sbt",
        ".sc",
        ".nim",
        ".zig",
        ".sol",
        ".proto",
        ".tf",
        ".hcl",
        ".ps1",
        ".psm1",
        ".psd1",
        ".bat",
        ".cmd",
        ".bash",
        ".zsh",
        ".fish",
        ".vue",
        ".svelte",
        ".sql",
        ".sh",
        ".pt",
    }
    LINE_COUNT_FILENAMES = {
        "dockerfile",
        "makefile",
        "cmakelists.txt",
        "jenkinsfile",
        "justfile",
    }
    MAX_LINE_COUNT_FILES = 450
    MAX_LINE_COUNT_FILE_SIZE = 220_000
    MAX_CONCURRENT_FILE_FETCHES = 24

    def __init__(self, token: str | None = None) -> None:
        """Create client with optional per-request token override."""

        settings = get_settings()
        self.base_url = settings.github_api_base.rstrip("/")
        runtime_token = token.strip() if isinstance(token, str) else None
        self.token = runtime_token or settings.github_app_token or settings.github_token
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "repo-inspector",
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    async def check_repo_access(self, owner: str, repo: str) -> None:
        """Validate repository visibility and token access."""

        await self._request("GET", f"/repos/{owner}/{repo}")

    async def _request(self, method: str, path: str, params: dict[str, Any] | None = None) -> Any:
        """Perform one GitHub API request with consistent error handling."""

        url = f"{self.base_url}{path}"
        timeout = httpx.Timeout(20.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.request(method, url, headers=self.headers, params=params)
            except httpx.HTTPError as exc:
                detail = self._http_error_detail(exc)
                raise GitHubAPIError(f"GitHub request failed: {detail}") from exc

        payload: Any = None
        try:
            payload = response.json()
        except ValueError:
            payload = None

        if response.status_code in (401, 403):
            detail = (
                payload.get("message")
                if isinstance(payload, dict)
                else "Unauthorized or rate-limited by GitHub API."
            )
            raise GitHubAPIError(f"GitHub API error ({response.status_code}): {detail}")
        if response.status_code >= 400:
            detail = (
                payload.get("message")
                if isinstance(payload, dict)
                else response.text[:200] or "Unknown error"
            )
            raise GitHubAPIError(f"GitHub API error ({response.status_code}): {detail}")
        if payload is not None:
            return payload
        raise GitHubAPIError("GitHub API returned non-JSON response.")

    @staticmethod
    def _http_error_detail(exc: httpx.HTTPError) -> str:
        """Extract stable, human-readable text from httpx exceptions."""

        direct = str(exc).strip()
        if direct:
            return direct

        cause = exc.__cause__ or exc.__context__
        if cause:
            nested = str(cause).strip()
            if nested:
                return nested

        if isinstance(exc, httpx.ConnectTimeout):
            return "Connection timed out while reaching GitHub API."
        if isinstance(exc, httpx.ReadTimeout):
            return "GitHub API did not respond in time."
        if isinstance(exc, httpx.ConnectError):
            return "Could not establish network connection to GitHub API."
        if isinstance(exc, httpx.TimeoutException):
            return "GitHub API request timed out."
        return f"{exc.__class__.__name__} while contacting GitHub API."

    @staticmethod
    def _parse_dt(value: str | None) -> datetime | None:
        """Parse ISO8601 timestamp from GitHub payload."""

        if not value:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    @staticmethod
    def _safe_int(value: object, default: int = 0) -> int:
        """Safely cast integer-like values."""

        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    async def get_repo_snapshot(
        self,
        owner: str,
        repo: str,
        line_count_fetch_limit: int | None = None,
    ) -> RepoSnapshot:
        """Fetch repository snapshot required for quality checks."""

        repo_data = await self._request("GET", f"/repos/{owner}/{repo}")
        default_branch = repo_data.get("default_branch")
        if not default_branch:
            raise GitHubAPIError("Repository default branch is not available.")
        default_branch_sha: str | None = None
        try:
            branch_data = await self._request("GET", f"/repos/{owner}/{repo}/branches/{default_branch}")
            commit_data = branch_data.get("commit", {}) if isinstance(branch_data, dict) else {}
            sha = commit_data.get("sha")
            if isinstance(sha, str):
                default_branch_sha = sha
        except GitHubAPIError:
            default_branch_sha = None

        tree = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/git/trees/{default_branch}",
            params={"recursive": 1},
        )
        tree_items = tree.get("tree", [])
        tree_paths = [item["path"] for item in tree_items if item.get("type") == "blob" and "path" in item]
        path_sizes = {
            item["path"]: int(item.get("size", 0))
            for item in tree_items
            if item.get("type") == "blob" and "path" in item
        }

        workflow_paths = [
            path
            for path in tree_paths
            if path.lower().startswith(".github/workflows/") and path.lower().endswith((".yml", ".yaml"))
        ]

        release_data = await self._request("GET", f"/repos/{owner}/{repo}/releases", params={"per_page": 1})
        tags_data = await self._request("GET", f"/repos/{owner}/{repo}/tags", params={"per_page": 1})
        has_release_or_tag = bool(release_data) or bool(tags_data)

        has_license = bool(repo_data.get("license"))
        if not has_license:
            try:
                await self._request("GET", f"/repos/{owner}/{repo}/license")
                has_license = True
            except GitHubAPIError:
                has_license = False

        line_count_paths, line_count_candidates_total = self._pick_line_count_files(tree_paths, path_sizes)
        line_count_paths = self._apply_line_count_fetch_limit(line_count_paths, line_count_fetch_limit)
        line_count_sampled = line_count_candidates_total > len(line_count_paths)
        important_files = self._pick_important_files(tree_paths, workflow_paths, line_count_paths)
        file_contents = await self._fetch_files(owner, repo, important_files, default_branch)

        return RepoSnapshot(
            owner=owner,
            name=repo,
            url=repo_data.get("html_url", f"https://github.com/{owner}/{repo}"),
            default_branch=default_branch,
            default_branch_sha=default_branch_sha,
            updated_at=self._parse_dt(repo_data.get("updated_at")),
            pushed_at=self._parse_dt(repo_data.get("pushed_at")),
            tree_paths=tree_paths,
            file_contents=file_contents,
            has_license=has_license,
            has_release_or_tag=has_release_or_tag,
            workflow_paths=workflow_paths,
            line_count_paths=line_count_paths,
            line_count_candidates_total=line_count_candidates_total,
            line_count_sampled=line_count_sampled,
        )

    async def get_changed_files_between_commits(
        self,
        owner: str,
        repo: str,
        base_sha: str,
        head_sha: str,
        max_files: int = 200,
    ) -> list[str]:
        if not base_sha or not head_sha or base_sha == head_sha:
            return []
        payload = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/compare/{base_sha}...{head_sha}",
            params={"per_page": max_files},
        )
        files = payload.get("files", []) if isinstance(payload, dict) else []
        changed: list[str] = []
        for item in files:
            if not isinstance(item, dict):
                continue
            filename = item.get("filename")
            if isinstance(filename, str):
                changed.append(filename)
        return changed[:max_files]

    async def get_repo_public_stats(self, owner: str, repo: str) -> RepoPublicStats:
        repo_data = await self._request("GET", f"/repos/{owner}/{repo}")
        languages_raw = await self._request("GET", f"/repos/{owner}/{repo}/languages")
        release_data = await self._request("GET", f"/repos/{owner}/{repo}/releases", params={"per_page": 1})
        tags_data = await self._request("GET", f"/repos/{owner}/{repo}/tags", params={"per_page": 1})

        languages: dict[str, int] = {}
        if isinstance(languages_raw, dict):
            for key, value in languages_raw.items():
                if not isinstance(key, str):
                    continue
                try:
                    amount = int(value)
                except (TypeError, ValueError):
                    continue
                if amount > 0:
                    languages[key] = amount

        topics = repo_data.get("topics")
        if not isinstance(topics, list):
            topics = []

        license_data = repo_data.get("license")
        license_name = None
        if isinstance(license_data, dict):
            maybe = license_data.get("spdx_id") or license_data.get("name")
            if isinstance(maybe, str):
                license_name = maybe

        return RepoPublicStats(
            owner=owner,
            name=repo,
            full_name=str(repo_data.get("full_name", f"{owner}/{repo}")),
            html_url=str(repo_data.get("html_url", f"https://github.com/{owner}/{repo}")),
            description=repo_data.get("description")
            if isinstance(repo_data.get("description"), str)
            else None,
            stars=self._safe_int(repo_data.get("stargazers_count")),
            forks=self._safe_int(repo_data.get("forks_count")),
            open_issues=self._safe_int(repo_data.get("open_issues_count")),
            watchers=self._safe_int(repo_data.get("subscribers_count", repo_data.get("watchers_count", 0))),
            default_branch=str(repo_data.get("default_branch", "main")),
            primary_language=(
                repo_data.get("language") if isinstance(repo_data.get("language"), str) else None
            ),
            license_name=license_name,
            topics=[str(item) for item in topics[:20]],
            archived=bool(repo_data.get("archived", False)),
            is_fork=bool(repo_data.get("fork", False)),
            size_kb=self._safe_int(repo_data.get("size")),
            created_at=self._parse_dt(repo_data.get("created_at")),
            updated_at=self._parse_dt(repo_data.get("updated_at")),
            pushed_at=self._parse_dt(repo_data.get("pushed_at")),
            homepage=repo_data.get("homepage") if isinstance(repo_data.get("homepage"), str) else None,
            has_releases=bool(release_data),
            has_tags=bool(tags_data),
            languages=languages,
        )

    @staticmethod
    def _pick_important_files(
        tree_paths: list[str],
        workflow_paths: list[str],
        line_count_paths: list[str],
    ) -> list[str]:
        important = set(workflow_paths)
        important.update(line_count_paths)
        for path in tree_paths:
            lower = path.lower()
            filename = lower.split("/")[-1]
            if filename.startswith("readme."):
                important.add(path)
            if filename == "contributing.md":
                important.add(path)
            if filename.startswith("license"):
                important.add(path)
            if filename == "pyproject.toml":
                important.add(path)
            if filename == ".pre-commit-config.yaml":
                important.add(path)
            if filename == ".env.example":
                important.add(path)
            if filename == "package.json":
                important.add(path)
            if filename in {"pom.xml", "build.gradle", "build.gradle.kts"}:
                important.add(path)
            if filename in {"directory.build.props", "stylecop.json", ".editorconfig"}:
                important.add(path)
            if filename in {
                "requirements.txt",
                "requirements-dev.txt",
                "poetry.lock",
                "pdm.lock",
                "package-lock.json",
                "pnpm-lock.yaml",
                "yarn.lock",
                "cargo.toml",
                "cargo.lock",
                "go.mod",
                "go.sum",
                "gemfile",
                "gemfile.lock",
                "composer.json",
                "composer.lock",
                "pubspec.yaml",
                "pubspec.lock",
                "analysis_options.yaml",
                "dart_test.yaml",
            }:
                important.add(path)
            if filename in {"security.md", "codeowners"}:
                important.add(path)
            if lower.startswith(".github/issue_template/"):
                important.add(path)
            if lower.startswith(".github/pull_request_template"):
                important.add(path)
            if lower == ".github/dependabot.yml":
                important.add(path)
            if filename in {
                ".repo-inspector.yml",
                ".repo-inspector.yaml",
                "repo-inspector.yml",
                "repo-inspector.yaml",
            }:
                important.add(path)
        return sorted(important)

    def _pick_line_count_files(
        self,
        tree_paths: list[str],
        path_sizes: dict[str, int],
    ) -> tuple[list[str], int]:
        candidates: list[str] = []
        for path in tree_paths:
            lower = path.lower()
            filename = lower.split("/")[-1]
            if filename.startswith("."):
                continue
            ext = self._extension(lower)
            if ext not in self.LINE_COUNT_EXTENSIONS and filename not in self.LINE_COUNT_FILENAMES:
                continue
            if path_sizes.get(path, 0) > self.MAX_LINE_COUNT_FILE_SIZE:
                continue
            candidates.append(path)
        candidates = sorted(candidates)
        total = len(candidates)
        if total > self.MAX_LINE_COUNT_FILES:
            candidates = candidates[: self.MAX_LINE_COUNT_FILES]
        return candidates, total

    @staticmethod
    def _apply_line_count_fetch_limit(paths: list[str], limit: int | None) -> list[str]:
        if limit is None:
            return paths
        try:
            parsed = int(limit)
        except (TypeError, ValueError):
            return paths
        if parsed <= 0:
            return []
        return paths[:parsed]

    @staticmethod
    def _extension(path: str) -> str:
        idx = path.rfind(".")
        return path[idx:] if idx >= 0 else ""

    async def _fetch_files(self, owner: str, repo: str, paths: list[str], ref: str) -> dict[str, str]:
        contents: dict[str, str] = {}
        if not paths:
            return contents
        async with httpx.AsyncClient(timeout=httpx.Timeout(20.0)) as client:
            semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_FILE_FETCHES)
            tasks = [
                self._fetch_single_file_guarded(client, semaphore, owner, repo, path, ref)
                for path in paths
            ]
            responses = await asyncio.gather(*tasks)

        for path, response in zip(paths, responses, strict=False):
            if response is None:
                continue
            contents[path] = response
        return contents

    async def _fetch_single_file_guarded(
        self,
        client: httpx.AsyncClient,
        semaphore: asyncio.Semaphore,
        owner: str,
        repo: str,
        path: str,
        ref: str,
    ) -> str | None:
        async with semaphore:
            return await self._fetch_single_file(client, owner, repo, path, ref)

    async def _fetch_single_file(
        self,
        client: httpx.AsyncClient,
        owner: str,
        repo: str,
        path: str,
        ref: str,
    ) -> str | None:
        try:
            response = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/contents/{path}",
                headers=self.headers,
                params={"ref": ref},
            )
        except httpx.HTTPError:
            return None
        if response.status_code >= 400:
            return None
        try:
            payload = response.json()
        except ValueError:
            return None
        encoded = payload.get("content")
        if not encoded or payload.get("encoding") != "base64":
            return None
        try:
            return base64.b64decode(encoded).decode("utf-8", errors="replace")
        except Exception:
            return None
