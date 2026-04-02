from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WAVES_ROOT = ROOT / "waves"


def git_output(*args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(ROOT), *args],
        text=True,
    ).strip()


def changed_paths_for_commit(commit: str) -> list[str]:
    output = git_output(
        "show",
        "--pretty=format:",
        "--name-only",
        "--diff-filter=AMR",
        commit,
    )
    return [line for line in output.splitlines() if line]


def build_cases(
    changed_paths: list[str],
) -> tuple[list[dict[str, object]], int, int]:
    test_files = {path for path in changed_paths if path.endswith(".rac.test")}
    rac_files = [
        path
        for path in changed_paths
        if path.endswith(".rac") and not path.endswith(".rac.test")
    ]

    cases: list[dict[str, object]] = []
    for index, path in enumerate(sorted(rac_files), 1):
        current_companion = ROOT / f"{path}.test"
        repo_test_path = (
            f"{path}.test"
            if current_companion.exists()
            else None
        )
        cases.append(
            {
                "index": index,
                "name": Path(path).stem,
                "citation_path": path.removeprefix("statute/").removesuffix(".rac"),
                "repo_rac_path": path,
                "repo_test_path": repo_test_path,
            }
        )

    available_companion_test_count = sum(
        1 for case in cases if case["repo_test_path"] is not None
    )
    return cases, len(test_files), available_companion_test_count


def build_seeded_from(args: argparse.Namespace) -> dict[str, object]:
    seeded_from: dict[str, object] = {
        "change_kind": args.change_kind,
    }
    if args.suite_manifest:
        seeded_from["suite_manifest"] = args.suite_manifest
    if args.suite_results_json:
        seeded_from["suite_results_json"] = args.suite_results_json
    if args.source_eval_run:
        seeded_from["source_eval_runs"] = list(args.source_eval_run)
    if args.autorac_commit:
        seeded_from["autorac_commit"] = args.autorac_commit
    if args.autorac_version:
        seeded_from["autorac_version"] = args.autorac_version
    if args.runner:
        seeded_from["runner"] = args.runner
    if args.notes:
        seeded_from["notes"] = args.notes
    return seeded_from


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a rac-us wave provenance manifest from a rac-us commit."
    )
    parser.add_argument("--wave", required=True, help="Wave directory name, e.g. 2026-04-02-wave6")
    parser.add_argument(
        "--source-commit",
        required=True,
        help="rac-us commit that introduced the files for this wave.",
    )
    parser.add_argument(
        "--provenance-tier",
        default="full",
        help="Manifest provenance tier, e.g. full, backfilled_git_history, or manual_repo_change.",
    )
    parser.add_argument(
        "--change-kind",
        default="encoding",
        help="High-level kind for seeded_from, e.g. encoding, supporting_stubs, maintenance.",
    )
    parser.add_argument("--autorac-commit")
    parser.add_argument("--autorac-version")
    parser.add_argument("--runner")
    parser.add_argument("--suite-manifest")
    parser.add_argument("--suite-results-json")
    parser.add_argument("--source-eval-run", action="append")
    parser.add_argument("--notes")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write the manifest to waves/<wave>/manifest.json. Otherwise print JSON to stdout.",
    )
    args = parser.parse_args()

    commit_subject = git_output("show", "-s", "--format=%s", args.source_commit)
    commit_date = git_output("show", "-s", "--format=%ci", args.source_commit)
    changed_paths = changed_paths_for_commit(args.source_commit)
    cases, changed_companion_test_count, available_companion_test_count = build_cases(
        changed_paths
    )

    manifest = {
        "wave": args.wave,
        "provenance_tier": args.provenance_tier,
        "created_from": {
            "rac_us_commit": args.source_commit,
            "commit_date": commit_date,
            "commit_subject": commit_subject,
        },
        "seeded_from": build_seeded_from(args),
        "summary": {
            "rac_file_count": len(cases),
            "changed_companion_test_count": changed_companion_test_count,
            "available_companion_test_count": available_companion_test_count,
        },
        "cases": cases,
    }

    payload = json.dumps(manifest, indent=2) + "\n"
    if not args.write:
        print(payload, end="")
        return 0

    out_dir = WAVES_ROOT / args.wave
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "manifest.json"
    out_path.write_text(payload)
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
