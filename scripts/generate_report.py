"""CLI utility to generate localized report JSON without running API server."""

from __future__ import annotations

import argparse
import asyncio
import json
import re
from pathlib import Path

from app.github_client import GitHubClient
from app.scanner.checks import detect_stacks, project_line_metrics, run_all_checks
from app.scanner.i18n import localize_report, normalize_lang
from app.scanner.policy import load_repo_policy
from app.scanner.scoring import build_report

REPO_RE = re.compile(r"^https?://github\.com/([^/\s]+)/([^/\s#]+?)(?:\.git)?/?$")


def parse_repo_url(repo_url: str) -> tuple[str, str]:
    """Parse and validate GitHub repository URL."""

    match = REPO_RE.match(repo_url.strip())
    if not match:
        raise ValueError("Invalid repo URL. Expected https://github.com/<owner>/<repo>")
    return match.group(1), match.group(2)


async def run(repo_url: str, output_dir: str, lang: str) -> Path:
    """Run full scan and save report JSON to disk."""

    owner, repo = parse_repo_url(repo_url)
    client = GitHubClient()
    snapshot = await client.get_repo_snapshot(owner, repo)
    policy = load_repo_policy(snapshot)
    checks = run_all_checks(snapshot, enable_network=True, policy=policy)
    stacks = detect_stacks(snapshot)
    metrics = project_line_metrics(snapshot)
    report = build_report(
        repo_owner=snapshot.owner,
        repo_name=snapshot.name,
        repo_url=snapshot.url,
        checks_by_category=checks,
        project_metrics=metrics,
        detected_stacks=stacks,
        category_weights=policy.category_weights,
        commit_sha=snapshot.default_branch_sha,
        policy_issues=policy.validation_errors,
    ).model_dump(mode="json")
    report = localize_report(report, normalize_lang(lang))

    destination_dir = Path(output_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{owner}__{repo}.{normalize_lang(lang)}.json"
    destination = destination_dir / filename
    destination.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return destination


def main() -> None:
    """CLI entrypoint."""

    parser = argparse.ArgumentParser(description="Generate Repo Inspector report JSON.")
    parser.add_argument("--repo-url", required=True, help="GitHub repository URL")
    parser.add_argument("--output-dir", default="web/reports", help="Directory for report JSON output")
    parser.add_argument("--lang", default="en", choices=["en", "ru"], help="Report language")
    args = parser.parse_args()

    output = asyncio.run(run(args.repo_url, args.output_dir, args.lang))
    print(f"Report generated: {output.as_posix()}")


if __name__ == "__main__":
    main()

