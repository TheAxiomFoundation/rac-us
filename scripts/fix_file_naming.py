#!/usr/bin/env python3
"""Fix .rac file naming to use subsection names instead of descriptive names.

Pattern: statute/26/61/a/1/wages.rac -> statute/26/61/a/1.rac
         statute/26/62/a/adjusted_gross_income.rac -> statute/26/62/a.rac
"""

import os
import re
import shutil
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent / "statute"


def is_subsection_name(name: str) -> bool:
    """Check if name is a valid subsection (short, no underscores)."""
    return len(name) <= 3 and '_' not in name


def get_files_to_fix() -> list[tuple[Path, Path]]:
    """Return list of (old_path, new_path) for files that need fixing."""
    fixes = []

    for rac_file in ROOT.rglob("*.rac"):
        stem = rac_file.stem

        if is_subsection_name(stem):
            continue  # Already correct

        parent = rac_file.parent
        parent_name = parent.name

        # Case 1: File is in a numbered/lettered subdirectory
        # e.g., statute/26/61/a/1/wages.rac -> statute/26/61/a/1.rac
        if is_subsection_name(parent_name):
            new_path = parent.parent / f"{parent_name}.rac"
            fixes.append((rac_file, new_path))
        else:
            # Case 2: File is at a level that should be a subsection
            # e.g., statute/26/61/gross_income.rac -> need to determine from context
            # For now, skip these - they need manual review
            print(f"SKIP (needs manual): {rac_file.relative_to(ROOT.parent)}")

    return fixes


def collect_variables(path: Path) -> list[str]:
    """Extract variable names from a .rac file."""
    content = path.read_text()
    # Match 'variable name:' pattern
    return re.findall(r'^variable\s+(\w+):', content, re.MULTILINE)


def merge_files(files: list[Path], target: Path):
    """Merge multiple .rac files into one."""
    contents = []
    seen_text = False

    for f in sorted(files):
        content = f.read_text()
        lines = content.strip().split('\n')

        # Skip duplicate headers/text blocks after first file
        filtered_lines = []
        in_text = False
        for line in lines:
            if line.strip().startswith('text:'):
                if seen_text:
                    in_text = True
                    continue
                seen_text = True
            if in_text:
                if line.startswith('variable') or line.startswith('parameter'):
                    in_text = False
                else:
                    continue
            if not line.startswith('#') or not seen_text:  # Keep first file's comments
                filtered_lines.append(line)

        contents.append('\n'.join(filtered_lines))

    target.write_text('\n\n'.join(contents))


def update_imports(content: str, old_to_new: dict[str, str]) -> str:
    """Update import paths in content."""
    for old, new in old_to_new.items():
        # Handle both path#var and just path patterns
        content = content.replace(old + '#', new + '#')
        content = content.replace(old + '"', new + '"')
        content = content.replace(old + '\n', new + '\n')
    return content


def main():
    # Step 1: Find all files that need fixing
    fixes = get_files_to_fix()
    print(f"\nFound {len(fixes)} files to fix")

    # Step 2: Group by target path (to handle merges)
    by_target = defaultdict(list)
    for old, new in fixes:
        by_target[new].append(old)

    # Step 3: Build import path mapping
    import_map = {}
    for old, new in fixes:
        old_import = str(old.relative_to(ROOT))[:-4]  # Remove .rac
        new_import = str(new.relative_to(ROOT))[:-4]
        import_map[old_import] = new_import

    # Step 4: Perform renames/merges
    for target, sources in by_target.items():
        if len(sources) == 1:
            # Simple rename
            print(f"RENAME: {sources[0].relative_to(ROOT.parent)} -> {target.relative_to(ROOT.parent)}")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(sources[0], target)
        else:
            # Merge multiple files
            print(f"MERGE: {[s.name for s in sources]} -> {target.relative_to(ROOT.parent)}")
            merge_files(sources, target)
            for s in sources:
                s.unlink()

    # Step 5: Clean up empty directories
    for dirpath, dirnames, filenames in os.walk(ROOT, topdown=False):
        if not dirnames and not filenames:
            os.rmdir(dirpath)
            print(f"RMDIR: {dirpath}")

    # Step 6: Update imports in all files
    print("\nUpdating imports...")
    for rac_file in ROOT.rglob("*.rac"):
        content = rac_file.read_text()
        new_content = update_imports(content, import_map)
        if content != new_content:
            print(f"  Updated imports in: {rac_file.relative_to(ROOT.parent)}")
            rac_file.write_text(new_content)

    print("\nDone!")


if __name__ == "__main__":
    main()
