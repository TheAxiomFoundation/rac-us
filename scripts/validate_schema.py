#!/usr/bin/env python3
"""Validate .rac files only use whitelisted attributes."""

import re
import sys
from pathlib import Path

# WHITELIST: Only these top-level attributes are allowed
ALLOWED_ATTRIBUTES = {
    # Required variable attributes
    "entity",
    "period",
    "dtype",
    # Optional variable attributes
    "unit",
    "label",
    "description",
    "formula",
    "default",
    "defined_for",
    # Block declarations
    "imports",
    "parameters",
    "exports",
    "examples",
    "tests",
    # Multi-variable file constructs (followed by identifier)
    "variable",
    "input",
    "enum",
    "values",
    "parameter",  # Named parameter declaration
    # Helper functions (followed by identifier)
    "function",
    # Raw statute text
    "text",
}

# Keywords that can appear in formula/function bodies (not attributes)
CODE_KEYWORDS = {
    "if", "else", "return", "for", "break",
    "and", "or", "not", "in",
}

def validate_filename(filepath: Path) -> list[str]:
    """Validate filename matches citation pattern.

    Valid: statute/26/32/a/1.rac -> 26 USC 32(a)(1)
    Invalid: statute/26/32/eitc.rac (descriptive name, not citation)
    """
    errors = []

    # Get path relative to statute/
    try:
        rel_path = filepath.relative_to(filepath.parent.parent.parent.parent / "statute")
    except ValueError:
        return errors  # Not under statute/

    parts = rel_path.parts

    # First part should be title number
    if not parts[0].isdigit():
        errors.append(f"{filepath}: first directory must be title number, got '{parts[0]}'")
        return errors

    # Filename (without .rac) should be a valid subsection identifier
    filename = filepath.stem

    # Valid: single letter (a-z), single digit (1-9), roman numeral (i, ii, iii, iv, v)
    valid_patterns = [
        r'^[a-z]$',           # Single letter: a, b, c
        r'^[1-9][0-9]*$',     # Number: 1, 2, 10
        r'^[ivxlcdm]+$',      # Roman numeral: i, ii, iii, iv
        r'^[A-Z]$',           # Capital letter: A, B, C
    ]

    import re
    is_valid = any(re.match(p, filename) for p in valid_patterns)

    if not is_valid:
        # Check if it's a descriptive name (invalid)
        if filename.lower() in ['eitc', 'ctc', 'snap', 'standard_deduction', 'agi']:
            errors.append(
                f"{filepath}: filename must be citation identifier, not descriptive name. "
                f"Use the subsection letter/number instead of '{filename}'"
            )
        elif len(filename) > 3 and not filename.isdigit():
            errors.append(
                f"{filepath}: filename '{filename}' doesn't look like a citation identifier. "
                f"Expected letter (a-z), number (1-9), or roman numeral (i, ii, iii)"
            )

    return errors


def validate_file(filepath: Path) -> list[str]:
    """Validate a single .rac file."""
    errors = []

    # Check filename first
    errors.extend(validate_filename(filepath))

    content = filepath.read_text()
    lines = content.split('\n')

    in_code_section = False  # Inside formula/function/defined_for
    in_multiline_string = False  # Inside """ block

    for lineno, line in enumerate(lines, 1):
        # Handle multiline strings (text: """ blocks)
        if '"""' in line:
            count = line.count('"""')
            if count == 1:
                in_multiline_string = not in_multiline_string
            # If count == 2, it opens and closes on same line
            continue
        if in_multiline_string:
            continue

        # Skip empty lines
        if not line.strip():
            continue

        # Skip comment lines
        stripped = line.strip()
        if stripped.startswith('#'):
            continue

        # Calculate indentation
        indent = len(line) - len(line.lstrip())

        # Only check lines with no indentation (top-level declarations)
        if indent > 0:
            continue

        # Check for named variable/input/function pattern: "variable name:" or "function name(...):"
        named_match = re.match(r'^(variable|input|function|enum)\s+([a-z_][a-z0-9_]*)', stripped)
        if named_match:
            attr = named_match.group(1)
            if attr == "function":
                in_code_section = True
            if attr not in ALLOWED_ATTRIBUTES:
                errors.append(f"{filepath}:{lineno}: forbidden attribute '{attr}'")
            continue

        # Check for attribute pattern: word followed by space, colon, or end of line
        match = re.match(r'^([a-z_]+)(:|\s|$)', stripped)
        if not match:
            # Line doesn't start with a word - could be assignment inside code
            # e.g., "tax = tax + ..." - these should only appear in code sections
            if in_code_section:
                continue
            # Check if it's an assignment (variable = ...)
            if re.match(r'^[a-z_]+\s*=', stripped):
                if not in_code_section:
                    errors.append(f"{filepath}:{lineno}: assignment outside code block")
            continue

        attr = match.group(1)

        # Check if this is a code keyword (part of formula/function body)
        if attr in CODE_KEYWORDS:
            if not in_code_section:
                errors.append(f"{filepath}:{lineno}: code keyword '{attr}' outside code block")
            continue

        # Check if entering a code section
        if attr in {"formula", "function", "defined_for"}:
            in_code_section = True
            if attr not in ALLOWED_ATTRIBUTES:
                errors.append(f"{filepath}:{lineno}: forbidden attribute '{attr}'")
            continue

        # If we hit a known attribute, we're leaving any code section
        if attr in ALLOWED_ATTRIBUTES:
            in_code_section = False
            continue

        # Unknown attribute - check if we're in code section (might be a variable name)
        if in_code_section:
            # Inside code, unknown words are likely variable assignments
            continue

        # Not in code, not a known attribute - this is a violation
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
