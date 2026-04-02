from __future__ import annotations

import argparse
import json
from pathlib import Path

import report_embedded_scalars


def load_baseline(path: Path) -> dict[tuple[str, int, str, str], dict[str, object]]:
    rows = json.loads(path.read_text())
    return {
        (
            str(row["file"]),
            int(row["line"]),
            str(row["variable"]),
            str(row["literal"]),
        ): row
        for row in rows
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail on new or worsened embedded scalar literal violations relative to the tracked baseline."
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
        help="Baseline JSON path (defaults to <root>/validation_baselines/embedded_scalars.json).",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    baseline_path = (
        args.baseline or root / "validation_baselines" / "embedded_scalars.json"
    ).resolve()
    current_rows = report_embedded_scalars.build_report(root)
    current = {
        (
            str(row["file"]),
            int(row["line"]),
            str(row["variable"]),
            str(row["literal"]),
        ): row
        for row in current_rows
    }
    baseline = load_baseline(baseline_path)

    regressions: list[str] = []
    improvements: list[str] = []

    for key, row in current.items():
        if key not in baseline:
            regressions.append(
                f"{row['file']}:{row['line']} {row['variable']} newly embeds "
                f"{row['literal']} in `{row['expression']}`"
            )

    for key, row in baseline.items():
        if key not in current:
            improvements.append(
                f"{row['file']}:{row['line']} {row['variable']} no longer embeds "
                f"{row['literal']}"
            )

    if regressions:
        print("Embedded scalar literal regressions detected:")
        for message in regressions:
            print(f"- {message}")
        if improvements:
            print("Improvements also detected:")
            for message in improvements:
                print(f"- {message}")
        return 1

    print(
        "Embedded scalar literal coverage matches or improves on the tracked baseline "
        f"({len(current_rows)} current violation row(s), {len(baseline)} baseline row(s))."
    )
    if improvements:
        print("Improvements:")
        for message in improvements:
            print(f"- {message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
