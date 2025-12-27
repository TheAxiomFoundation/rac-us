"""Enforce that .rac filenames are subsections, not descriptive names."""

import pytest
from pathlib import Path


def get_invalid_rac_files():
    """Find .rac files with invalid names (descriptive instead of subsection)."""
    root = Path(__file__).parent.parent / "statute"
    errors = []
    
    for rac_file in root.rglob("*.rac"):
        stem = rac_file.stem
        
        # Valid: single letter/number subsection (1, a, B, i, ii, 2A, etc.)
        # Invalid: descriptive names (wages, dividend_income, gross_income, etc.)
        if '_' in stem or len(stem) > 3:
            rel_path = rac_file.relative_to(root.parent)
            errors.append(str(rel_path))
    
    return errors


class TestFileNaming:
    """All .rac files must use subsection names, not descriptive names."""

    def test_rac_filenames_are_subsections(self):
        """
        Filenames must be the legal subsection (1.rac, a.rac, B.rac), 
        NOT descriptive names (wages.rac, gross_income.rac).
        
        WRONG: statute/26/61/a/1/wages.rac
        RIGHT: statute/26/61/a/1.rac
        """
        errors = get_invalid_rac_files()
        
        if errors:
            msg = f"\n\n{len(errors)} files have invalid names:\n"
            for e in errors[:20]:  # Show first 20
                msg += f"  - {e}\n"
            if len(errors) > 20:
                msg += f"  ... and {len(errors) - 20} more\n"
            msg += "\nFilenames must be subsections (1, a, B), not descriptive names."
            pytest.fail(msg)
