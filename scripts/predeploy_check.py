"""Pre-deployment checks for Repo Inspector project."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(slots=True)
class CheckResult:
    """One pre-deploy check result."""

    name: str
    ok: bool
    details: str


def _check_file_exists(path: Path, name: str) -> CheckResult:
    """Ensure file exists."""

    if path.exists():
        return CheckResult(name=name, ok=True, details=f"found: {path.as_posix()}")
    return CheckResult(name=name, ok=False, details=f"missing: {path.as_posix()}")


def _check_config(path: Path) -> CheckResult:
    """Validate required config structure in config.yml."""

    if not path.exists():
        return CheckResult(name="config.yml", ok=False, details="config.yml not found")
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        return CheckResult(name="config.yml", ok=False, details=f"YAML parse error: {exc}")
    if not isinstance(payload, dict):
        return CheckResult(name="config.yml", ok=False, details="config root must be mapping")

    required = {
        ("app", "name"),
        ("github", "api_base"),
        ("database", "url"),
        ("scan", "cache_ttl_seconds"),
    }
    missing: list[str] = []
    for section, key in required:
        section_value = payload.get(section)
        if not isinstance(section_value, dict) or key not in section_value:
            missing.append(f"{section}.{key}")
    if missing:
        return CheckResult(name="config.yml", ok=False, details=f"missing keys: {', '.join(missing)}")
    return CheckResult(name="config.yml", ok=True, details="required keys present")


def _check_vercel_routes(path: Path) -> CheckResult:
    """Validate vercel.json route essentials for API deployment."""

    if not path.exists():
        return CheckResult(name="vercel.json", ok=False, details="vercel.json not found")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return CheckResult(name="vercel.json", ok=False, details=f"JSON parse error: {exc}")
    if not isinstance(payload, dict):
        return CheckResult(name="vercel.json", ok=False, details="root must be object")

    routes = payload.get("routes")
    if not isinstance(routes, list):
        return CheckResult(name="vercel.json", ok=False, details="routes must be array")
    route_src = {str(item.get("src")) for item in routes if isinstance(item, dict)}
    required_src = {"/api", "/api/(.*)", "/health"}
    missing = sorted(src for src in required_src if src not in route_src)
    if missing:
        return CheckResult(name="vercel.json", ok=False, details=f"missing routes: {', '.join(missing)}")
    return CheckResult(name="vercel.json", ok=True, details="required routes present")


def _check_workflow_hardening(workflow_dir: Path) -> CheckResult:
    """Check workflow files for timeout settings."""

    if not workflow_dir.exists():
        return CheckResult(name="workflows", ok=False, details=".github/workflows not found")
    workflow_files = sorted(workflow_dir.glob("*.yml")) + sorted(workflow_dir.glob("*.yaml"))
    if not workflow_files:
        return CheckResult(name="workflows", ok=False, details="no workflow files found")

    without_timeout: list[str] = []
    for path in workflow_files:
        content = path.read_text(encoding="utf-8", errors="replace")
        if "timeout-minutes:" not in content:
            without_timeout.append(path.name)
    if without_timeout:
        return CheckResult(
            name="workflows",
            ok=False,
            details=f"timeout-minutes missing in: {', '.join(without_timeout)}",
        )
    return CheckResult(name="workflows", ok=True, details="timeout-minutes configured")


def _run_command(command: list[str], cwd: Path) -> CheckResult:
    """Execute one command and return structured result."""

    proc = subprocess.run(command, cwd=str(cwd), capture_output=True, text=True)
    output = (proc.stdout or proc.stderr or "").strip().splitlines()
    tail = output[-1] if output else "ok"
    ok = proc.returncode == 0
    return CheckResult(
        name=" ".join(command),
        ok=ok,
        details=tail if ok else f"failed ({proc.returncode}): {tail}",
    )


def run_checks(root: Path, strict: bool) -> list[CheckResult]:
    """Run all pre-deploy checks."""

    results: list[CheckResult] = [
        _check_file_exists(root / "README.md", "README.md"),
        _check_file_exists(root / "README_EN.md", "README_EN.md"),
        _check_file_exists(root / "CHANGELOG.md", "CHANGELOG.md"),
        _check_file_exists(root / "SUPPORT.md", "SUPPORT.md"),
        _check_file_exists(root / ".editorconfig", ".editorconfig"),
        _check_config(root / "config.yml"),
        _check_vercel_routes(root / "vercel.json"),
        _check_workflow_hardening(root / ".github" / "workflows"),
    ]
    if strict:
        results.append(_run_command(["ruff", "check", "."], root))
        results.append(_run_command(["pytest", "-q"], root))
    return results


def _print_summary(results: list[CheckResult]) -> int:
    """Print text summary and return process exit code."""

    failed = [item for item in results if not item.ok]
    for item in results:
        status = "OK" if item.ok else "FAIL"
        print(f"[{status}] {item.name}: {item.details}")
    if failed:
        print(f"\nPre-deploy checks failed: {len(failed)}")
        return 1
    print(f"\nPre-deploy checks passed: {len(results)}")
    return 0


def main() -> None:
    """CLI entrypoint."""

    parser = argparse.ArgumentParser(description="Run Repo Inspector pre-deployment checks.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Run additional quality gates (ruff + pytest).",
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    results = run_checks(root, strict=args.strict)
    raise SystemExit(_print_summary(results))


if __name__ == "__main__":
    main()
