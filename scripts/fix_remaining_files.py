#!/usr/bin/env python3
"""Fix remaining .rac files with descriptive names.

These files are at section level and need to be merged into a single file
or renamed to a proper subsection.
"""

import shutil
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent / "statute"


def is_subsection_name(name: str) -> bool:
    """Check if name is a valid subsection (short, no underscores)."""
    return len(name) <= 3 and '_' not in name


def get_invalid_files() -> list[Path]:
    """Get all files with invalid names."""
    invalid = []
    for rac_file in ROOT.rglob("*.rac"):
        stem = rac_file.stem
        if not is_subsection_name(stem):
            invalid.append(rac_file)
    return invalid


def merge_files_at_level(section_dir: Path, target_name: str = "a"):
    """Merge all descriptive-named files in a directory into one file."""
    invalid_files = []
    valid_files = []

    for f in section_dir.glob("*.rac"):
        if is_subsection_name(f.stem):
            valid_files.append(f)
        else:
            invalid_files.append(f)

    if not invalid_files:
        return

    # Target is the section-level a.rac or the section itself
    if valid_files:
        # Append to existing valid file (first one alphabetically)
        target = sorted(valid_files)[0]
        mode = 'append'
    else:
        # Create new a.rac
        target = section_dir / f"{target_name}.rac"
        mode = 'create'

    print(f"\nMerging {len(invalid_files)} files into {target.relative_to(ROOT.parent)}:")
    for f in sorted(invalid_files):
        print(f"  - {f.name}")

    contents = []

    # Read existing target if appending
    if mode == 'append' and target.exists():
        contents.append(target.read_text())

    # Read all invalid files
    for f in sorted(invalid_files):
        content = f.read_text().strip()
        # Add separator
        contents.append(f"\n\n# ---- Merged from {f.name} ----\n")
        contents.append(content)

    # Write merged content
    target.write_text('\n'.join(contents))

    # Remove old files
    for f in invalid_files:
        f.unlink()


def handle_section(section_path: Path, merge_target: str = "a"):
    """Handle a section with invalid files."""
    merge_files_at_level(section_path, merge_target)


def main():
    # Group invalid files by their parent directory
    invalid = get_invalid_files()
    by_parent = defaultdict(list)
    for f in invalid:
        by_parent[f.parent].append(f)

    print(f"Found {len(invalid)} invalid files in {len(by_parent)} directories")

    for parent, files in sorted(by_parent.items()):
        rel = parent.relative_to(ROOT)
        print(f"\n{rel}/: {len(files)} files")

        # Determine merge target
        # Check if there's already a valid file to merge into
        valid_files = [f for f in parent.glob("*.rac") if is_subsection_name(f.stem)]

        if valid_files:
            target = sorted(valid_files)[0].stem
        else:
            # Use 'a' as default subsection
            target = "a"

        handle_section(parent, target)

    # Verify
    remaining = get_invalid_files()
    if remaining:
        print(f"\n\nStill have {len(remaining)} invalid files:")
        for f in remaining:
            print(f"  - {f.relative_to(ROOT.parent)}")
    else:
        print("\n\nAll files now have valid subsection names!")


if __name__ == "__main__":
    main()
