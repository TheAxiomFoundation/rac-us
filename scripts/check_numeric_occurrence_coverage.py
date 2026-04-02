from __future__ import annotations

import argparse
import json
from pathlib import Path

import report_numeric_occurrence_coverage


def load_baseline(path: Path) -> dict[tuple[str, float], dict[str, object]]:
    rows = json.loads(path.read_text())
    return {
        (str(row["file"]), float(row["value"])): row
        for row in rows
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail on new or worsened source-number coverage gaps relative to the tracked baseline."
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
        help="Baseline JSON path (defaults to <root>/validation_baselines/numeric_occurrence_coverage.json).",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    baseline_path = (
        args.baseline
        or root / "validation_baselines" / "numeric_occurrence_coverage.json"
    ).resolve()
    current_rows = report_numeric_occurrence_coverage.build_report(root)
    current = {
        (str(row["file"]), float(row["value"])): row
        for row in current_rows
    }
    baseline = load_baseline(baseline_path)

    regressions: list[str] = []
    improvements: list[str] = []

    for key, row in current.items():
        baseline_row = baseline.get(key)
        if baseline_row is None:
            regressions.append(
                f"{row['file']} value {row['value']:g} is a new coverage gap "
                f"({row['source_count']} source occurrence(s), {row['named_count']} named definition(s))."
            )
            continue

        if int(row["missing_count"]) > int(baseline_row["missing_count"]):
            regressions.append(
                f"{row['file']} value {row['value']:g} worsened from "
                f"{baseline_row['missing_count']} missing occurrence(s) to {row['missing_count']}."
            )
        elif int(row["missing_count"]) < int(baseline_row["missing_count"]):
            improvements.append(
                f"{row['file']} value {row['value']:g} improved from "
                f"{baseline_row['missing_count']} missing occurrence(s) to {row['missing_count']}."
            )

    for key, row in baseline.items():
        if key not in current:
            improvements.append(
                f"{row['file']} value {row['value']:g} is fully covered now."
            )

    if regressions:
        print("Numeric occurrence coverage regressions detected:")
        for message in regressions:
            print(f"- {message}")
        if improvements:
            print("Improvements also detected:")
            for message in improvements:
                print(f"- {message}")
        return 1

    print(
        "Numeric occurrence coverage matches or improves on the tracked baseline "
        f"({len(current_rows)} current gap row(s), {len(baseline)} baseline row(s))."
    )
    if improvements:
        print("Improvements:")
        for message in improvements:
            print(f"- {message}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
