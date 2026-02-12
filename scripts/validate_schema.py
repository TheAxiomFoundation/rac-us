#!/usr/bin/env python3
"""Validate .rac files use valid attributes, definition names, and values."""

import re
import sys
from pathlib import Path

VALID_ENTITIES = {
    "Person", "TaxUnit", "Household", "Family",
    "TanfUnit", "SnapUnit", "SPMUnit",
    "Corporation", "Business", "Asset",
}
VALID_PERIODS = {"Year", "Month", "Week", "Day"}
VALID_DTYPES = {"Money", "Rate", "Boolean", "Integer", "Count", "String", "Decimal", "Float"}

ALLOWED_ATTRIBUTES = {
    "entity", "period", "dtype", "unit", "label", "description",
    "formula", "default", "defined_for",
    "imports", "parameters", "exports", "examples",
    "variable", "input", "enum", "values", "parameter",
    "function", "text", "tests",
}

CODE_KEYWORDS = {
    "if", "else", "return", "for", "break",
    "and", "or", "not", "in",
}

ENTITY_PATTERN = re.compile(r"^\s*entity:\s*(\w+)")
PERIOD_PATTERN = re.compile(r"^\s*period:\s*(Year|Month|Week|Day|[A-Z][a-z]+)$")
DTYPE_PATTERN = re.compile(r"^\s*dtype:\s*(\w+)")
PARAMETER_PATTERN = re.compile(r"^parameter\s+(\w+):")
LEGISLATION_ANTIPATTERNS = [
    (r"pre_tcja|post_tcja|tcja_", "TCJA"),
    (r"pre_aca|post_aca|aca_", "ACA"),
    (r"pre_arpa|post_arpa|arpa_", "ARPA"),
    (r"pre_arra|post_arra|arra_", "ARRA"),
    (r"pre_tra|post_tra|tra97_|tra01_", "TRA"),
    (r"_2017_|_2018_|_2019_|_2020_|_2021_|_2022_|_2023_|_2024_", "year"),
]
FORMULA_START = re.compile(r"^\s*formula:\s*\|")
FORMULA_LINE = re.compile(r"^\s{4,}")
TEMPORAL_ENTRY_PATTERN = re.compile(r"^\s+from\s+\d{4}-\d{2}-\d{2}:")
BARE_DEFINITION_PATTERN = re.compile(r"^([a-z_][a-z0-9_]*):\s*(?!\|)")

LITERAL_PATTERN = re.compile(
    r"""
    (?<![a-zA-Z_\d])  # Not preceded by identifier char or digit
    (
        \d+\.\d+      # Float like 0.075
        |
        [4-9]         # Single digit 4-9
        |
        [1-9]\d+      # Multi-digit starting with 1-9 (10+)
    )
    (?![a-zA-Z_\d])   # Not followed by identifier char or digit
    """,
    re.VERBOSE,
)

def validate_file(filepath: Path) -> list[str]:
    """Validate a single .rac file."""
    errors = []
    content = filepath.read_text()
    lines = content.split('\n')

    in_code_section = False
    in_formula = False
    in_multiline_string = False

    for lineno, line in enumerate(lines, 1):
        if '"""' in line:
            count = line.count('"""')
            if count == 1:
                in_multiline_string = not in_multiline_string
            # If count == 2, it opens and closes on same line
            continue
        if in_multiline_string:
            continue

        if FORMULA_START.match(line):
            in_formula = True
            continue
        elif in_formula and not FORMULA_LINE.match(line) and line.strip():
            in_formula = False

        if in_formula:
            code_line = re.sub(r"#.*$", "", line)
            code_line = re.sub(r"['\"].*?['\"]", "", code_line)

            for match in LITERAL_PATTERN.finditer(code_line):
                literal = match.group(1)
                try:
                    val = float(literal)
                    if val in {-1.0, 0.0, 1.0, 2.0, 3.0}:
                        continue
                except ValueError:
                    pass
                errors.append(f"{filepath}:{lineno}: hardcoded literal '{literal}' - use a parameter instead")

        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue

        if TEMPORAL_ENTRY_PATTERN.match(line):
            continue

        param_match = PARAMETER_PATTERN.match(stripped)
        if param_match:
            param_name = param_match.group(1)
            for pattern, legislation in LEGISLATION_ANTIPATTERNS:
                if re.search(pattern, param_name, re.IGNORECASE):
                    errors.append(
                        f"{filepath}:{lineno}: parameter '{param_name}' references {legislation} - "
                        f"use time-varying values instead (e.g., 2017-12-15: new_value)"
                    )

        entity_match = ENTITY_PATTERN.match(line)
        if entity_match:
            entity = entity_match.group(1)
            if entity not in VALID_ENTITIES:
                errors.append(f"{filepath}:{lineno}: invalid entity '{entity}' (must be one of: {sorted(VALID_ENTITIES)})")

        period_match = PERIOD_PATTERN.match(line)
        if period_match:
            period = period_match.group(1)
            if period not in VALID_PERIODS:
                errors.append(f"{filepath}:{lineno}: invalid period '{period}' (must be one of: {sorted(VALID_PERIODS)})")

        dtype_match = DTYPE_PATTERN.match(line)
        if dtype_match:
            dtype = dtype_match.group(1)
            if dtype not in VALID_DTYPES and not dtype.startswith("Enum"):
                errors.append(f"{filepath}:{lineno}: invalid dtype '{dtype}' (must be one of: {sorted(VALID_DTYPES)} or Enum[...])")

        indent = len(line) - len(line.lstrip())
        if indent > 0:
            continue

        named_match = re.match(r'^(variable|input|function|enum)\s+([a-z_][a-z0-9_]*)', stripped)
        if named_match:
            if named_match.group(1) == "function":
                in_code_section = True
            continue

        match = re.match(r'^([a-z_]+)(:|\s|$)', stripped)
        if not match:
            if in_code_section:
                continue
            if re.match(r'^[a-z_]+\s*=', stripped):
                errors.append(f"{filepath}:{lineno}: assignment outside code block")
            continue

        attr = match.group(1)

        if attr in CODE_KEYWORDS:
            if not in_code_section:
                errors.append(f"{filepath}:{lineno}: code keyword '{attr}' outside code block")
            continue

        if attr in {"formula", "function", "defined_for"}:
            in_code_section = True
            continue

        if attr in ALLOWED_ATTRIBUTES:
            in_code_section = False
            continue

        # Bare definition name in unified syntax (e.g. "snap_allotment:")
        if BARE_DEFINITION_PATTERN.match(line):
            in_code_section = False
            continue

        if in_code_section:
            continue

        errors.append(f"{filepath}:{lineno}: forbidden attribute '{attr}'")

    return errors

def main():
    statute_dir = Path(__file__).parent.parent / "statute"

    if not statute_dir.exists():
        print(f"Error: {statute_dir} not found")
        sys.exit(1)

    all_errors = []
    files_checked = 0

    for rac_file in statute_dir.rglob("*.rac"):
        files_checked += 1
        errors = validate_file(rac_file)
        all_errors.extend(errors)

    print(f"Checked {files_checked} .rac files")
    print(f"Allowed attributes: {sorted(ALLOWED_ATTRIBUTES)}")

    if all_errors:
        print(f"\n❌ Found {len(all_errors)} violations:\n")
        for error in sorted(all_errors):
            print(f"  {error}")
        sys.exit(1)
    else:
        print("\n✅ All files pass schema validation")
        sys.exit(0)

if __name__ == "__main__":
    main()
