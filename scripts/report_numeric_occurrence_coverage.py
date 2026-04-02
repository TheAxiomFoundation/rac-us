from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

import repo_layout


DATE_PATTERN = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
PERCENT_WORD_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s+(?:percent|per\s*cent(?:um)?)", re.IGNORECASE
)
PERCENT_SIGN_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*%")
SOURCE_NUMBER_PATTERN = re.compile(r"(?:^|(?<=[\s$£€(\[,]))(-?[\d,]+(?:\.\d+)?)\b")
STRUCTURAL_LINE_PATTERN = re.compile(
    r"^[\(\[]?(?:\d+[A-Za-z]?|[ivxlcdm]+|[a-z])[\)\].]?$", re.IGNORECASE
)
STRUCTURAL_HEADING_PATTERN = re.compile(
    r"^(PART|CHAPTER|SCHEDULE|REGULATION|ARTICLE)\b", re.IGNORECASE
)
STRUCTURAL_PREFIX_PATTERN = re.compile(
    r"^\s*(?:\d+[A-Za-z]?\.\s+|\([0-9A-Za-zivxlcdm]+\)\s+)", re.IGNORECASE
)
SOURCE_REFERENCE_TARGET_PATTERN = (
    r"(?:\([^)]+\)|\d+[A-Za-z./-]*(?:\([^)]+\))*(?=$|[\s,.;:])|[ivxlcdm]+\b|[A-Z]{1,4}\b|[a-z]\b)"
)
SOURCE_REFERENCE_SEQUENCE_PATTERN = (
    rf"{SOURCE_REFERENCE_TARGET_PATTERN}"
    rf"(?:\s*(?:,|or|and)\s*{SOURCE_REFERENCE_TARGET_PATTERN})*"
)
SOURCE_REFERENCE_PATTERNS = (
    re.compile(
        r"\b(?:section|sections)\s+\d+[A-Za-z]?(?:\([^)]+\))*"
        r"(?:\s*,\s*\d+[A-Za-z]?(?:\([^)]+\))*)*"
        r"(?:\s*,?\s*(?:and|or)\s+\d+[A-Za-z]?(?:\([^)]+\))*)*",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:paragraph|paragraphs|subparagraph|subparagraphs|clause|clauses|subclause|subclauses)\s+"
        r"\([^)]+\)(?:\([^)]+\))*"
        r"(?:\s*,\s*\([^)]+\)(?:\([^)]+\))*)*"
        r"(?:\s*,?\s*(?:and|or)\s+\([^)]+\)(?:\([^)]+\))*)*",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:section|sections)\s+\d+[A-Za-z]?(?:\([^)]+\))+",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:paragraph|paragraphs|subparagraph|subparagraphs|clause|clauses|subclause|subclauses)\s+\([^)]+\)(?:\([^)]+\))*",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:section|sections|paragraph|paragraphs|regulation|regulations|part|parts|chapter|chapters|schedule|schedules|article|articles|subparagraph|subparagraphs|sub-paragraph|sub-paragraphs|subsection|subsections)\s+"
        rf"{SOURCE_REFERENCE_SEQUENCE_PATTERN}(?:\s+to\s+{SOURCE_REFERENCE_SEQUENCE_PATTERN})?",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:Act|Order|Regulations?)\s+\d{4}\b"),
)
BLOCK_HEADER_PATTERN = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*$")
TEMPORAL_LINE_PATTERN = re.compile(r"^(\s*)from\s+\d{4}-\d{2}-\d{2}:\s*(.*?)\s*$")
SCALAR_LINE_PATTERN = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(-?[\d,]+(?:\.\d+)?)\s*$")
DIRECT_SCALAR_PATTERN = re.compile(r"-?[\d,]+(?:\.\d+)?")
IMPORT_LINE_PATTERN = re.compile(
    r"^\s*-\s+(?P<path>[^#\s]+)#(?P<symbol>[A-Za-z_][A-Za-z0-9_]*)(?:\s+as\s+(?P<alias>[A-Za-z_][A-Za-z0-9_]*))?\s*$"
)
METADATA_KEYS = {
    "entity",
    "period",
    "dtype",
    "unit",
    "label",
    "description",
    "status",
    "indexed_by",
    "formula",
    "tests",
    "imports",
    "variable",
}
IGNORED_VALUES = {-1.0, 0.0, 1.0, 2.0, 3.0}


@dataclass(frozen=True)
class NamedScalarOccurrence:
    file: str
    line: int
    name: str
    value: float


@dataclass(frozen=True)
class NumericCoverageGap:
    file: str
    value: float
    source_count: int
    named_count: int
    missing_count: int


def extract_embedded_source_text(content: str) -> str:
    status_index = content.find("\nstatus:")
    header = content[:status_index] if status_index != -1 else content
    blocks = re.findall(r'"""(.*?)"""', header, re.DOTALL)
    if blocks:
        return "\n".join(block.strip() for block in blocks if block.strip())

    fallback_blocks = re.findall(r'"""(.*?)"""', content, re.DOTALL)
    return "\n".join(block.strip() for block in fallback_blocks if block.strip())


def extract_numeric_occurrences_from_text(text: str) -> list[float]:
    cleaned_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if STRUCTURAL_LINE_PATTERN.match(stripped):
            continue
        if STRUCTURAL_HEADING_PATTERN.match(stripped):
            continue
        cleaned_lines.append(STRUCTURAL_PREFIX_PATTERN.sub("", line))

    cleaned = "\n".join(cleaned_lines)
    cleaned = DATE_PATTERN.sub(" ", cleaned)
    for pattern in SOURCE_REFERENCE_PATTERNS:
        cleaned = pattern.sub(" ", cleaned)

    occurrences: list[float] = []
    percent_spans: list[tuple[int, int]] = []

    for pattern in (PERCENT_WORD_PATTERN, PERCENT_SIGN_PATTERN):
        for match in pattern.finditer(cleaned):
            occurrences.append(float(match.group(1).replace(",", "")) / 100)
            percent_spans.append(match.span())

    def overlaps_percent(span: tuple[int, int]) -> bool:
        return any(not (span[1] <= start or span[0] >= end) for start, end in percent_spans)

    for match in SOURCE_NUMBER_PATTERN.finditer(cleaned):
        span = match.span(1)
        if overlaps_percent(span):
            continue
        value = float(match.group(1).replace(",", ""))
        if value.is_integer() and 1900 <= value <= 2100:
            continue
        occurrences.append(value)

    occurrence_counts = Counter(occurrences)
    normalized: list[float] = []
    for value in occurrences:
        scaled = round(value * 100, 9)
        if value <= 1 and scaled in occurrence_counts:
            continue
        normalized.append(value)
    return normalized


def extract_named_scalar_occurrences(
    rac_file: Path, root: Path
) -> list[NamedScalarOccurrence]:
    occurrences: list[NamedScalarOccurrence] = []
    current_variable: str | None = None
    temporal_block = False
    temporal_indent = 0

    for line_number, line in enumerate(rac_file.read_text().splitlines(), 1):
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())

        header_match = BLOCK_HEADER_PATTERN.match(line)
        if header_match and indent == 0:
            current_variable = header_match.group(1)

        if temporal_block and stripped and indent <= temporal_indent:
            temporal_block = False

        scalar_match = SCALAR_LINE_PATTERN.match(stripped)
        if scalar_match:
            name = scalar_match.group(1)
            if name.lower() not in METADATA_KEYS:
                occurrences.append(
                    NamedScalarOccurrence(
                        file=str(rac_file.relative_to(root)),
                        line=line_number,
                        name=name,
                        value=float(scalar_match.group(2).replace(",", "")),
                    )
                )
            continue

        temporal_match = TEMPORAL_LINE_PATTERN.match(line)
        if temporal_match:
            temporal_indent = len(temporal_match.group(1))
            tail = temporal_match.group(2).strip().replace(",", "")
            if tail and DIRECT_SCALAR_PATTERN.fullmatch(tail):
                occurrences.append(
                    NamedScalarOccurrence(
                        file=str(rac_file.relative_to(root)),
                        line=line_number,
                        name=current_variable or "<unknown>",
                        value=float(tail),
                    )
                )
                temporal_block = False
            else:
                temporal_block = True
            continue

        if temporal_block and stripped:
            normalized = stripped.replace(",", "")
            if DIRECT_SCALAR_PATTERN.fullmatch(normalized):
                occurrences.append(
                    NamedScalarOccurrence(
                        file=str(rac_file.relative_to(root)),
                        line=line_number,
                        name=current_variable or "<unknown>",
                        value=float(normalized),
                    )
                )

    return occurrences


def extract_import_targets(rac_file: Path) -> list[tuple[str, str]]:
    targets: list[tuple[str, str]] = []
    for line in rac_file.read_text().splitlines():
        match = IMPORT_LINE_PATTERN.match(line)
        if not match:
            continue
        targets.append((match.group("path"), match.group("symbol")))
    return targets


def imported_scalar_values(
    rac_file: Path,
    root: Path,
    cache: dict[tuple[str, str], list[float]],
) -> list[float]:
    values: list[float] = []
    content_root = repo_layout.content_root(root)
    for import_path, symbol in extract_import_targets(rac_file):
        key = (import_path, symbol)
        if key not in cache:
            target_file = content_root / f"{import_path}.rac"
            if not target_file.exists():
                cache[key] = []
            else:
                cache[key] = [
                    occurrence.value
                    for occurrence in extract_named_scalar_occurrences(target_file, root)
                    if occurrence.name == symbol
                ]
        values.extend(cache[key])
    return values


def build_report(root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    imported_scalar_cache: dict[tuple[str, str], list[float]] = {}

    for rac_file in sorted(repo_layout.content_root(root).rglob("*.rac")):
        if rac_file.name.endswith(".rac.test"):
            continue
        content = rac_file.read_text()
        source_text = extract_embedded_source_text(content)
        source_counts = Counter(extract_numeric_occurrences_from_text(source_text))
        named_counts = Counter(item.value for item in extract_named_scalar_occurrences(rac_file, root))
        named_counts.update(imported_scalar_values(rac_file, root, imported_scalar_cache))

        for value, source_count in sorted(source_counts.items()):
            if value in IGNORED_VALUES:
                continue
            named_count = named_counts.get(value, 0)
            if named_count >= source_count:
                continue
            rows.append(
                asdict(
                    NumericCoverageGap(
                        file=str(rac_file.relative_to(root)),
                        value=value,
                        source_count=source_count,
                        named_count=named_count,
                        missing_count=source_count - named_count,
                    )
                )
            )

    return rows


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report source numeric occurrences that are not represented by named RAC scalar definitions."
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
        print("All substantive source numbers are covered by named RAC scalar definitions.")
        return 0

    print("Numeric occurrence coverage gaps:")
    for row in rows:
        print(
            f"- {row['file']} value {row['value']:g} appears {row['source_count']} time(s) "
            f"in source text but only {row['named_count']} named scalar definition(s) were found"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
