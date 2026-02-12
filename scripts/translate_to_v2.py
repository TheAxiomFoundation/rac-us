#!/usr/bin/env python3
"""Translate RAC DSL v1 files to v2 syntax.

Changes:
- imports { } → imports:
- references { } → imports:
- variable name { } → remove wrapper (filename is name)
- formula { } → formula:
- defined_for { } → defined_for:
- parameters { } → parameters:
- Remove closing braces
- Remove module/version declarations
- Remove 'let' keywords
- Python-style indentation with :
"""

import re
from pathlib import Path


def translate_file(content: str) -> str:
    """Translate v1 syntax to v2."""
    lines = content.split('\n')
    result = []

    # Track state
    in_block = None
    brace_depth = 0

    i = 0
    while i < len(lines):
        line = lines[i]
        original_line = line
        stripped = line.strip()

        # Preserve empty lines
        if not stripped:
            result.append('')
            i += 1
            continue

        # Preserve comments
        if stripped.startswith('#'):
            if in_block in ('formula', 'defined_for', 'function', 'match'):
                result.append('  ' + stripped)
            else:
                result.append(stripped)
            i += 1
            continue

        # Skip module and version declarations
        if stripped.startswith('module ') or stripped.startswith('version '):
            i += 1
            continue

        # Convert imports/references block
        if stripped in ('imports {', 'references {'):
            result.append('imports:')
            in_block = 'imports'
            i += 1
            continue

        # Convert parameters block
        if stripped == 'parameters {':
            result.append('parameters:')
            in_block = 'parameters'
            i += 1
            continue

        # Skip variable wrapper - extract just the content
        if stripped.startswith('variable ') and stripped.endswith('{'):
            in_block = 'variable'
            brace_depth = 1
            i += 1
            continue

        # Convert formula block
        if stripped == 'formula {':
            result.append('')
            result.append('formula:')
            in_block = 'formula'
            i += 1
            continue

        # Convert defined_for block
        if stripped == 'defined_for {':
            result.append('')
            result.append('defined_for:')
            in_block = 'defined_for'
            i += 1
            continue

        # Handle closing braces
        if stripped == '}':
            if in_block == 'variable':
                brace_depth -= 1
                if brace_depth == 0:
                    in_block = None
            elif in_block in ('imports', 'parameters', 'formula', 'defined_for', 'function', 'match'):
                in_block = None
            i += 1
            continue

        # Inside imports/parameters - indent content
        if in_block in ('imports', 'parameters'):
            result.append('  ' + stripped)
            i += 1
            continue

        # Inside formula/defined_for - process content
        if in_block in ('formula', 'defined_for'):
            # Remove 'let' keyword
            processed = stripped
            if processed.startswith('let '):
                processed = processed[4:]

            result.append('  ' + processed)
            i += 1
            continue

        # Inside variable block - these become top-level
        if in_block == 'variable':
            # Track nested braces
            if stripped.endswith('{'):
                brace_depth += 1
            if stripped == '}':
                brace_depth -= 1
                if brace_depth == 0:
                    in_block = None
                i += 1
                continue

            # Handle formula/defined_for inside variable
            if stripped == 'formula {':
                result.append('')
                result.append('formula:')
                in_block = 'formula'
                i += 1
                continue
            if stripped == 'defined_for {':
                result.append('')
                result.append('defined_for:')
                in_block = 'defined_for'
                i += 1
                continue

            # Top-level attributes (entity, period, dtype, etc.)
            result.append(stripped)
            i += 1
            continue

        # Handle function definitions
        if stripped.startswith('function ') and stripped.endswith('{'):
            func_line = stripped[:-1].rstrip() + ':'
            result.append('')
            result.append(func_line)
            in_block = 'function'
            i += 1
            continue

        # Top-level content
        result.append(stripped)
        i += 1

    # Clean up multiple blank lines
    cleaned = []
    prev_blank = False
    for line in result:
        is_blank = line.strip() == ''
        if is_blank and prev_blank:
            continue
        cleaned.append(line)
        prev_blank = is_blank

    return '\n'.join(cleaned)


def process_file(filepath: Path, dry_run: bool = False) -> bool:
    """Process a single file. Returns True if changed."""
    content = filepath.read_text()

    # Skip if already v2 (has imports: with colon on its own line)
    if '\nimports:\n' in content:
        return False

    translated = translate_file(content)

    if dry_run:
        print(f"Would translate: {filepath}")
        return True

    filepath.write_text(translated)
    print(f"  Translated: {filepath.name}")
    return True


def main():
    """Main entry point."""
    import sys

    dry_run = '--dry-run' in sys.argv

    base_dir = Path('/Users/maxghenis/RulesFoundation/rac-us/statute')

    files = list(base_dir.rglob('*.rac'))
    print(f"Found {len(files)} .rac files")

    changed = 0
    for filepath in files:
        try:
            if process_file(filepath, dry_run=dry_run):
                changed += 1
        except Exception as e:
            print(f"  ERROR processing {filepath}: {e}")

    print(f"\nTranslated {changed} files")


if __name__ == '__main__':
    main()
