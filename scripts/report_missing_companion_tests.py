from __future__ import annotations

import argparse
import json
from pathlib import Path

import repo_layout


def build_report(root: Path) -> list[str]:
    content_root = repo_layout.content_root(root)
    missing: list[str] = []

    for rac_file in sorted(content_root.rglob("*.rac")):
        if rac_file.name.endswith(".rac.test"):
            continue
        companion = rac_file.with_suffix(rac_file.suffix + ".test")
        if not companion.exists():
            missing.append(str(rac_file.relative_to(root)))

    return missing


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report missing companion .rac.test files."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a text summary.",
    )
    args = parser.parse_args()

    rows = build_report(args.root.resolve())
    if args.json:
        print(json.dumps(rows, indent=2))
        return 0

    if not rows:
        print("All .rac files have companion .rac.test files.")
        return 0

    print("Missing companion .rac.test files:")
    for path in rows:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
