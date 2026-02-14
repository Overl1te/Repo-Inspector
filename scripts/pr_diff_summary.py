from __future__ import annotations

import argparse
from collections import Counter
from typing import Any

import httpx

from app.config import get_settings


def fetch_pr_files(owner: str, repo: str, pr_number: int, token: str) -> list[dict[str, Any]]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "repo-inspector",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    files: list[dict[str, Any]] = []
    page = 1
    with httpx.Client(timeout=httpx.Timeout(20.0)) as client:
        while True:
            response = client.get(
                f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files",
                headers=headers,
                params={"per_page": 100, "page": page},
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list) or not payload:
                break
            files.extend(payload)
            if len(payload) < 100:
                break
            page += 1
    return files


def render_markdown(files: list[dict[str, Any]]) -> str:
    if not files:
        return "### PR Diff\n\nNo changed files detected."

    status_counter = Counter()
    ext_counter = Counter()
    additions = 0
    deletions = 0
    for item in files:
        status = str(item.get("status", "modified"))
        status_counter[status] += 1
        filename = str(item.get("filename", ""))
        ext = _ext(filename)
        ext_counter[ext] += 1
        additions += int(item.get("additions", 0) or 0)
        deletions += int(item.get("deletions", 0) or 0)

    lines = [
        "### PR Diff",
        "",
        f"- Files changed: **{len(files)}**",
        f"- Additions: **{additions}**",
        f"- Deletions: **{deletions}**",
        "",
        "#### Change types",
    ]
    for status, count in status_counter.most_common():
        lines.append(f"- `{status}`: {count}")
    lines.extend(["", "#### Top extensions"])
    for ext, count in ext_counter.most_common(8):
        lines.append(f"- `{ext}`: {count}")
    return "\n".join(lines)


def _ext(path: str) -> str:
    if "." not in path:
        return "no_ext"
    return path.rsplit(".", 1)[-1].lower()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate markdown PR diff summary.")
    parser.add_argument("--owner", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--pr", required=True, type=int)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()

    settings = get_settings()
    token = settings.github_app_token or settings.github_token
    files = fetch_pr_files(args.owner, args.repo, args.pr, token)
    markdown = render_markdown(files)
    with open(args.output_file, "w", encoding="utf-8") as fh:
        fh.write(markdown)
    print(f"PR diff summary written: {args.output_file}")


if __name__ == "__main__":
    main()
