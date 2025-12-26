#!/usr/bin/env python3
"""Tests for DSL v1 to v2 translation."""

import pytest
from translate_to_v2 import translate_file


class TestImportsBlock:
    """Test imports/references block translation."""

    def test_imports_block_converts_braces_to_colon(self):
        v1 = '''imports {
  foo: path/to/foo
  bar: path/to/bar
}'''
        v2 = translate_file(v1)
        assert 'imports:' in v2
        assert 'imports {' not in v2
        assert '  foo: path/to/foo' in v2
        assert '}' not in v2

    def test_references_becomes_imports(self):
        v1 = '''references {
  foo: path/to/foo
}'''
        v2 = translate_file(v1)
        assert 'imports:' in v2
        assert 'references' not in v2


class TestVariableBlock:
    """Test variable block unwrapping."""

    def test_variable_wrapper_removed(self):
        v1 = '''variable earned_income_credit {
  entity TaxUnit
  period Year
  dtype Money
}'''
        v2 = translate_file(v1)
        assert 'variable ' not in v2
        assert 'entity TaxUnit' in v2
        assert 'period Year' in v2
        assert 'dtype Money' in v2
        assert '{' not in v2
        assert '}' not in v2


class TestFormulaBlock:
    """Test formula block translation."""

    def test_formula_braces_to_colon(self):
        v1 = '''formula {
    credit = income * rate
    return credit
  }'''
        v2 = translate_file(v1)
        assert 'formula:' in v2
        assert 'formula {' not in v2
        assert '  credit = income * rate' in v2
        assert '}' not in v2

    def test_formula_with_if_then_else(self):
        v1 = '''formula {
    result = if x > 0 then x else 0
    return result
  }'''
        v2 = translate_file(v1)
        assert 'formula:' in v2
        assert 'if x > 0 then x else 0' in v2


class TestDefinedForBlock:
    """Test defined_for block translation."""

    def test_defined_for_braces_to_colon(self):
        v1 = '''defined_for {
    income > 0
  }'''
        v2 = translate_file(v1)
        assert 'defined_for:' in v2
        assert 'defined_for {' not in v2
        assert '  income > 0' in v2


class TestModuleAndVersion:
    """Test module/version removal."""

    def test_module_line_removed(self):
        v1 = '''module statute.26.32
version "2024.1"

entity TaxUnit'''
        v2 = translate_file(v1)
        assert 'module ' not in v2
        assert 'version ' not in v2
        assert 'entity TaxUnit' in v2


class TestCommentsPreserved:
    """Test that comments are preserved."""

    def test_hash_comments_preserved(self):
        v1 = '''# This is a comment
# Another comment

entity TaxUnit'''
        v2 = translate_file(v1)
        assert '# This is a comment' in v2
        assert '# Another comment' in v2


class TestLetKeyword:
    """Test let keyword removal."""

    def test_let_removed_from_assignments(self):
        v1 = '''formula {
    let x = 10
    let y = x + 20
    return y
  }'''
        v2 = translate_file(v1)
        assert 'let ' not in v2
        assert '  x = 10' in v2
        assert '  y = x + 20' in v2


class TestCompleteFile:
    """Test complete file translation."""

    def test_full_file_translation(self):
        v1 = '''# 26 USC Section 32 - Earned Income Credit

module statute.26.32.a.1
version "2024.1"

imports {
  earned_income: statute/26/32/c/2/A/earned_income
  agi: statute/26/62/a/adjusted_gross_income
}

variable earned_income_credit {
  entity TaxUnit
  period Year
  dtype Money
  default 0

  formula {
    credit = earned_income * rate
    return min(credit, max_credit)
  }

  defined_for {
    earned_income > 0
  }
}
'''
        v2 = translate_file(v1)

        # Check structure
        assert '# 26 USC Section 32 - Earned Income Credit' in v2
        assert 'module ' not in v2
        assert 'version ' not in v2
        assert 'imports:' in v2
        assert '  earned_income: statute/26/32/c/2/A/earned_income' in v2
        assert 'variable ' not in v2
        assert 'entity TaxUnit' in v2
        assert 'period Year' in v2
        assert 'dtype Money' in v2
        assert 'default 0' in v2
        assert 'formula:' in v2
        assert '  credit = earned_income * rate' in v2
        assert 'defined_for:' in v2
        assert '  earned_income > 0' in v2
        assert '{' not in v2
        assert '}' not in v2


class TestParametersBlock:
    """Test parameters block translation."""

    def test_parameters_braces_to_colon(self):
        v1 = '''parameters {
  rate: 0.34
  max_credit: 6000
}'''
        v2 = translate_file(v1)
        assert 'parameters:' in v2
        assert 'parameters {' not in v2
        assert '  rate: 0.34' in v2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
