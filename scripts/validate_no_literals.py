#!/usr/bin/env python3
"""Validate .rac formulas have no hardcoded numeric literals (except 0, 1, -1, and small indices 2, 3)."""

import re
import sys
from pathlib import Path

# Allowed small integers (for indexing, child counts, etc.)
ALLOWED_INTEGERS = {-1, 0, 1, 2, 3}

# Attributes that start new variable definitions (exit formula context)
VARIABLE_ATTRIBUTES = {
    "entity", "period", "dtype", "unit", "label", "description",
    "default", "defined_for", "imports", "parameters", "exports",
    "examples", "variable", "input", "enum", "values", "function",
}

def find_numeric_violations(filepath: Path) -> list[str]:
    """Find numeric literals in formula blocks that aren't allowed."""
    errors = []
    content = filepath.read_text()
    lines = content.split('\n')

    in_formula = False

    for lineno, line in enumerate(lines, 1):
        stripped = line.strip()

        # Skip empty lines and comments
        if not stripped or stripped.startswith('#'):
            continue

        # Skip lines that are just string literals (label, description, etc.)
        if stripped.startswith('"') or stripped.startswith("'"):
            continue

        # Check for formula start
        if stripped.startswith('formula:'):
            in_formula = True
            continue

        # Check for exit from formula (new attribute at indent 0)
        indent = len(line) - len(line.lstrip())
        if indent == 0:
            first_word = stripped.split()[0].rstrip(':') if stripped.split() else ''
            if first_word in VARIABLE_ATTRIBUTES:
                in_formula = False
                continue

        if not in_formula:
            continue

        # Skip lines with string literals (contain quotes)
        if '"' in stripped or "'" in stripped:
            continue

        # Skip inline comments
        if '#' in stripped:
            stripped = stripped[:stripped.index('#')]

        # Find numeric literals in comparisons and assignments
        # Match patterns like: >= 65, == 0.075, < 100
        for match in re.finditer(r'(>=|<=|>|<|==|!=|\+|-|\*|/)\s*(-?\d+\.?\d*)', stripped):
            num_str = match.group(2)
            try:
                if '.' in num_str:
                    # Decimal - always a violation (should be a rate parameter)
                    errors.append(f"{filepath}:{lineno}: decimal literal {num_str}")
                else:
                    num = int(num_str)
                    if num not in ALLOWED_INTEGERS:
                        errors.append(f"{filepath}:{lineno}: integer literal {num}")
            except ValueError:
                pass

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
        errors = find_numeric_violations(rac_file)
        all_errors.extend(errors)

    print(f"Checked {files_checked} .rac files for numeric literals")
    print(f"Allowed integers: {sorted(ALLOWED_INTEGERS)}")

    if all_errors:
        print(f"\n❌ Found {len(all_errors)} violations:\n")
        for error in sorted(all_errors):
            print(f"  {error}")
        sys.exit(1)
    else:
        print("\n✅ No forbidden numeric literals found")
        sys.exit(0)

if __name__ == "__main__":
    main()
