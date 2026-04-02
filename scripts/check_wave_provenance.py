from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def git_lines(*args: str) -> list[str]:
    output = subprocess.check_output(
        ["git", "-C", str(ROOT), *args],
        text=True,
    ).strip()
    return [line for line in output.splitlines() if line]


def changed_files(base: str, head: str) -> list[str]:
    return git_lines("diff", "--name-only", f"{base}...{head}")


def changed_rac_files(paths: list[str]) -> list[str]:
    return sorted(
        path
        for path in paths
        if path.startswith("statute/")
        and path.endswith(".rac")
        and not path.endswith(".rac.test")
    )


def changed_manifest_files(paths: list[str]) -> list[Path]:
    return sorted(
        ROOT / path
        for path in paths
        if path.startswith("waves/") and path.endswith("/manifest.json")
    )


def covered_rac_paths(manifest_paths: list[Path]) -> set[str]:
    covered: set[str] = set()
    for path in manifest_paths:
        payload = json.loads(path.read_text())
        for case in payload.get("cases", []):
            rac_path = case.get("repo_rac_path")
            if isinstance(rac_path, str):
                covered.add(rac_path)
    return covered


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Require changed rac-us .rac files to be covered by a changed wave manifest."
    )
    parser.add_argument("--base", required=True, help="Base git ref or commit.")
    parser.add_argument("--head", required=True, help="Head git ref or commit.")
    args = parser.parse_args()

    paths = changed_files(args.base, args.head)
    rac_paths = changed_rac_files(paths)
    if not rac_paths:
        print("No .rac files changed; wave provenance check skipped.")
        return 0

    manifest_paths = changed_manifest_files(paths)
    if not manifest_paths:
        print(
            "Changed .rac files detected but no wave manifest changed. "
            "Add or update waves/<date>-waveN/manifest.json in the same change.",
            file=sys.stderr,
        )
        for path in rac_paths:
            print(f"- {path}", file=sys.stderr)
        return 1

    covered = covered_rac_paths(manifest_paths)
    missing = [path for path in rac_paths if path not in covered]
    if missing:
        print(
            "Changed .rac files are not covered by the changed wave manifest(s):",
            file=sys.stderr,
        )
        for path in missing:
            print(f"- {path}", file=sys.stderr)
        print("Changed manifest(s):", file=sys.stderr)
        for path in manifest_paths:
            print(f"- {path.relative_to(ROOT)}", file=sys.stderr)
        return 1

    print(
        "Wave provenance check passed: all changed .rac files are covered by the changed manifest(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
