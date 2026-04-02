from __future__ import annotations

import argparse
import json
from pathlib import Path

import report_missing_companion_tests


def load_baseline(path: Path) -> set[str]:
    return set(json.loads(path.read_text()))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail on new or worsened missing companion .rac.test files relative to the tracked baseline."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root.",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=None,
        help="Baseline JSON path (defaults to <root>/validation_baselines/missing_companion_tests.json).",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    baseline_path = (
        args.baseline or root / "validation_baselines" / "missing_companion_tests.json"
    ).resolve()
    current = set(report_missing_companion_tests.build_report(root))
    baseline = load_baseline(baseline_path)

    regressions = sorted(current - baseline)
    improvements = sorted(baseline - current)

    if regressions:
        print("Companion .rac.test regressions detected:")
        for path in regressions:
            print(f"- {path}")
        if improvements:
            print("Improvements also detected:")
            for path in improvements:
                print(f"- {path}")
        return 1

    print(
        "Companion .rac.test coverage matches or improves on the tracked baseline "
        f"({len(current)} current missing file(s), {len(baseline)} baseline file(s))."
    )
    if improvements:
        print("Improvements:")
        for path in improvements:
            print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
