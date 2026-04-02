from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import repo_layout


BLOCK_HEADER = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*$")
TEMPORAL_LINE = re.compile(r"^(\s*)from\s+\d{4}-\d{2}-\d{2}:\s*(.*?)\s*$")
FORMULA_HEADER = re.compile(r"^(\s*)formula:\s*\|\s*$")
NUMBER_PATTERN = re.compile(r"-?\d+(?:\.\d+)?")
DIRECT_SCALAR_PATTERN = re.compile(r"-?[\d,]+(?:\.\d+)?")
ALLOWED_EMBEDDED_SCALARS = {"-1", "0", "1", "2", "3"}
QUOTED_STRING_PATTERN = re.compile(r"'[^']*'|\"[^\"]*\"")


@dataclass
class EmbeddedScalarViolation:
    file: str
    variable: str
    line: int
    literal: str
    expression: str


def _extract_embedded_literals(expression: str) -> list[str]:
    literals: list[str] = []
    scrubbed_expression = QUOTED_STRING_PATTERN.sub(" ", expression)
    for match in NUMBER_PATTERN.finditer(scrubbed_expression):
        start, end = match.span()
        prev = scrubbed_expression[start - 1] if start > 0 else ""
        nxt = scrubbed_expression[end] if end < len(scrubbed_expression) else ""
        if (prev.isalnum() or prev in {"_", ".", "/"}) or (
            nxt.isalnum() or nxt in {"_", ".", "/"}
        ):
            continue
        literal = match.group(0)
        if literal in ALLOWED_EMBEDDED_SCALARS:
            continue
        literals.append(literal)
    return sorted(set(literals))


def _is_direct_scalar_value(expression: str) -> bool:
    normalized = expression.replace(",", "")
    return bool(DIRECT_SCALAR_PATTERN.fullmatch(normalized))


def extract_embedded_scalar_violations(
    rac_file: Path,
    root: Path,
) -> list[EmbeddedScalarViolation]:
    lines = rac_file.read_text().splitlines()
    violations: list[EmbeddedScalarViolation] = []
    current_variable: str | None = None
    temporal_block = False
    temporal_indent = 0
    formula_block = False
    formula_indent = 0

    for line_number, line in enumerate(lines, 1):
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())

        header_match = BLOCK_HEADER.match(line)
        if header_match and indent == 0:
            current_variable = header_match.group(1)

        if temporal_block and stripped and indent <= temporal_indent:
            temporal_block = False
        if formula_block and stripped and indent <= formula_indent:
            formula_block = False

        temporal_match = TEMPORAL_LINE.match(line)
        if temporal_match:
            temporal_indent = len(temporal_match.group(1))
            tail = temporal_match.group(2).strip()
            if tail:
                if not _is_direct_scalar_value(tail):
                    for literal in _extract_embedded_literals(tail):
                        violations.append(
                            EmbeddedScalarViolation(
                                file=str(rac_file.relative_to(root)),
                                variable=current_variable or "<unknown>",
                                line=line_number,
                                literal=literal,
                                expression=tail,
                            )
                        )
                temporal_block = False
            else:
                temporal_block = True
            continue

        formula_match = FORMULA_HEADER.match(line)
        if formula_match:
            formula_block = True
            formula_indent = len(formula_match.group(1))
            continue

        if (temporal_block or formula_block) and stripped and not _is_direct_scalar_value(
            stripped
        ):
            for literal in _extract_embedded_literals(stripped):
                violations.append(
                    EmbeddedScalarViolation(
                        file=str(rac_file.relative_to(root)),
                        variable=current_variable or "<unknown>",
                        line=line_number,
                        literal=literal,
                        expression=stripped,
                    )
                )

    return violations


def build_report(root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for rac_file in sorted(repo_layout.content_root(root).rglob("*.rac")):
        if rac_file.name.endswith(".rac.test"):
            continue
        rows.extend(
            asdict(item)
            for item in extract_embedded_scalar_violations(rac_file, root)
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report embedded scalar literals inside RAC formulas."
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
        print("No embedded scalar literals found in formulas.")
        return 0

    print("Embedded scalar literals:")
    for row in rows:
        print(
            f"- {row['file']}:{row['line']} {row['variable']} embeds "
            f"{row['literal']} in `{row['expression']}`"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
