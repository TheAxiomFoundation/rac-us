#!/usr/bin/env python3
"""Convert old .rac format to new self-contained format.

Old format:
- variable name: at top level with nested imports/parameters refs
- parameters: references like parameters#gov.usda.fns.snap.allotment.max
- separate .yaml files for parameter values

New format:
- text: (triple-quoted) at top
- parameter name: with inline values
- variable name: with imports, tests
"""

import re
import yaml
from pathlib import Path
from typing import Any
from collections import defaultdict


def load_parameters_yaml(yaml_path: Path) -> dict:
    """Load and flatten parameter YAML into lookup dict."""
    if not yaml_path.exists():
        return {}

    try:
        with open(yaml_path) as f:
            data = yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Warning: Failed to load {yaml_path}: {e}")
        return {}

    # Flatten nested structure into dot-notation keys
    flat = {}

    def flatten(obj, prefix=""):
        if isinstance(obj, dict):
            # Check if this is a parameter value node (has 'values' or 'amounts' key)
            if 'values' in obj or 'amounts' in obj:
                flat[prefix.rstrip('.')] = obj
            else:
                for k, v in obj.items():
                    flatten(v, f"{prefix}{k}.")

    flatten(data)
    return flat


def find_all_param_yamls(statute_dir: Path) -> dict:
    """Find all parameter YAML files and load them."""
    all_params = {}
    for yaml_file in statute_dir.rglob("*.yaml"):
        if yaml_file.name in ("tests.yaml",):
            continue
        params = load_parameters_yaml(yaml_file)
        all_params.update(params)
    return all_params


def parse_old_rac(content: str) -> dict:
    """Parse old format .rac file."""
    result = {
        "header_comments": [],
        "variables": [],
    }

    lines = content.split('\n')
    i = 0

    # Collect header comments
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith('#') or not line.strip():
            result["header_comments"].append(line)
            i += 1
        else:
            break

    # Parse variables
    current_var = None
    current_indent = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # New variable declaration
        var_match = re.match(r'^variable\s+(\w+):', stripped)
        if var_match and not line.startswith(' '):
            if current_var:
                result["variables"].append(current_var)
            current_var = {
                "name": var_match.group(1),
                "attributes": {},
                "imports": [],
                "param_refs": [],
                "formula_lines": [],
                "raw_lines": [line],
            }
            i += 1
            continue

        if current_var:
            current_var["raw_lines"].append(line)

            # Parse attributes
            if stripped.startswith('entity '):
                current_var["attributes"]["entity"] = stripped.split()[1]
            elif stripped.startswith('period '):
                current_var["attributes"]["period"] = stripped.split()[1]
            elif stripped.startswith('dtype '):
                current_var["attributes"]["dtype"] = stripped.split()[1]
            elif stripped.startswith('unit '):
                current_var["attributes"]["unit"] = stripped.split('"')[1] if '"' in stripped else stripped.split()[1]
            elif stripped.startswith('label '):
                current_var["attributes"]["label"] = stripped.split('"')[1] if '"' in stripped else stripped.split()[1]
            elif stripped.startswith('description '):
                current_var["attributes"]["description"] = stripped.split('"')[1] if '"' in stripped else stripped.split(maxsplit=1)[1]
            elif stripped.startswith('default '):
                current_var["attributes"]["default"] = stripped.split()[1]

            # Parse imports
            import_match = re.match(r'^\s+(\w+):\s*statute/(.+)#(\w+)', stripped)
            if import_match:
                alias = import_match.group(1)
                path = import_match.group(2)
                var_name = import_match.group(3)
                current_var["imports"].append({
                    "alias": alias,
                    "path": path,
                    "variable": var_name
                })

            # Parse parameter references
            param_match = re.match(r'^\s+(\w+):\s*parameters#(.+)', stripped)
            if param_match:
                alias = param_match.group(1)
                param_path = param_match.group(2)
                current_var["param_refs"].append({
                    "alias": alias,
                    "path": param_path
                })

            # Track if we're in formula block
            if stripped.startswith('formula:'):
                in_formula = True

        i += 1

    if current_var:
        result["variables"].append(current_var)

    return result


def extract_text_from_comments(comments: list[str]) -> str:
    """Extract statute text from header comments."""
    text_lines = []
    in_quote = False

    for line in comments:
        stripped = line.lstrip('#').strip()
        # Look for quoted statute text
        if '"' in stripped or in_quote:
            if stripped.startswith('"'):
                in_quote = True
                stripped = stripped[1:]
            if stripped.endswith('"'):
                in_quote = False
                stripped = stripped[:-1]
            if stripped:
                text_lines.append(stripped)

    return '\n'.join(text_lines) if text_lines else None


def convert_to_new_format(old_content: str, params_lookup: dict, tests_lookup: dict = None) -> str:
    """Convert old format to new format."""
    parsed = parse_old_rac(old_content)

    lines = []

    # Header comment (file path comment)
    for comment in parsed["header_comments"][:2]:
        if comment.strip().startswith('#'):
            lines.append(comment)

    # Extract text from comments
    text = extract_text_from_comments(parsed["header_comments"])
    if text:
        lines.append('')
        lines.append('text: """')
        lines.append(text)
        lines.append('"""')

    # Collect all unique parameters used across variables
    all_param_refs = {}
    for var in parsed["variables"]:
        for ref in var["param_refs"]:
            all_param_refs[ref["alias"]] = ref["path"]

    # Emit parameters
    if all_param_refs:
        lines.append('')
        for alias, path in all_param_refs.items():
            param_data = params_lookup.get(path, {})
            lines.append(f'parameter {alias}:')
            if param_data.get('description'):
                lines.append(f'  description: "{param_data["description"]}"')
            if param_data.get('unit'):
                lines.append(f'  unit: {param_data["unit"]}')
            if param_data.get('reference'):
                lines.append(f'  source: "{param_data["reference"]}"')

            # Values
            if 'values' in param_data:
                lines.append('  values:')
                for date, value in sorted(param_data['values'].items(), reverse=True):
                    lines.append(f'    {date}: {value}')
            elif 'amounts' in param_data:
                lines.append('  values:')
                for date, value in sorted(param_data['amounts'].items(), reverse=True):
                    lines.append(f'    {date}: {value}')
            else:
                lines.append('  values:')
                lines.append('    # TODO: add values')
            lines.append('')

    # Emit variables
    for var in parsed["variables"]:
        lines.append(f'variable {var["name"]}:')

        # Imports
        if var["imports"]:
            import_strs = []
            for imp in var["imports"]:
                if imp["alias"] == imp["variable"]:
                    import_strs.append(f'{imp["path"]}#{imp["variable"]}')
                else:
                    import_strs.append(f'{imp["path"]}#{imp["variable"]} as {imp["alias"]}')
            lines.append(f'  imports: [{", ".join(import_strs)}]')

        # Standard attributes
        for attr in ["entity", "period", "dtype", "unit", "label", "description"]:
            if attr in var["attributes"]:
                val = var["attributes"][attr]
                if attr in ("unit", "label", "description"):
                    lines.append(f'  {attr}: "{val}"')
                else:
                    lines.append(f'  {attr}: {val}')

        # Formula - extract from raw lines
        in_formula = False
        formula_lines = []
        for raw_line in var["raw_lines"]:
            if raw_line.strip().startswith('formula:'):
                in_formula = True
                continue
            if in_formula:
                if raw_line.strip().startswith('default '):
                    break
                if raw_line.strip() and not raw_line.startswith('  '):
                    break
                formula_lines.append(raw_line)

        if formula_lines:
            # Check if single line or multi-line
            non_empty = [l for l in formula_lines if l.strip()]
            if len(non_empty) == 1:
                lines.append(f'  formula: {non_empty[0].strip()}')
            else:
                lines.append('  formula: |')
                for fl in formula_lines:
                    if fl.strip():
                        # Normalize indent to 4 spaces
                        lines.append(f'    {fl.strip()}')

        # Default
        if "default" in var["attributes"]:
            lines.append(f'  default: {var["attributes"]["default"]}')

        # Tests (if available)
        if tests_lookup and var["name"] in tests_lookup:
            lines.append('  tests:')
            for test in tests_lookup[var["name"]]:
                if test.get("name"):
                    lines.append(f'    - name: "{test["name"]}"')
                else:
                    lines.append('    -')
                if test.get("inputs"):
                    lines.append(f'      inputs: {test["inputs"]}')
                if test.get("expect") is not None:
                    lines.append(f'      expect: {test["expect"]}')

        lines.append('')

    return '\n'.join(lines)


def convert_file(rac_path: Path, params_lookup: dict, dry_run: bool = True) -> str:
    """Convert a single .rac file."""
    content = rac_path.read_text()

    # Skip files that are already in new format
    if content.strip().startswith('text:') or '\nparameter ' in content:
        return None

    # Skip v2 files (already converted)
    if '_v2.rac' in str(rac_path):
        return None

    new_content = convert_to_new_format(content, params_lookup)

    if not dry_run:
        # Write to new file (or overwrite)
        rac_path.write_text(new_content)

    return new_content


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Convert .rac files to new format")
    parser.add_argument("--dry-run", action="store_true", help="Don't write files, just print")
    parser.add_argument("--file", type=Path, help="Convert single file")
    parser.add_argument("--all", action="store_true", help="Convert all files")
    args = parser.parse_args()

    statute_dir = Path(__file__).parent.parent / "statute"
    params_lookup = find_all_param_yamls(statute_dir)
    print(f"Loaded {len(params_lookup)} parameters from YAML files")

    if args.file:
        result = convert_file(args.file, params_lookup, dry_run=args.dry_run)
        if result:
            print(result)
    elif args.all:
        converted = 0
        skipped = 0
        for rac_file in statute_dir.rglob("*.rac"):
            result = convert_file(rac_file, params_lookup, dry_run=args.dry_run)
            if result:
                converted += 1
                if args.dry_run:
                    print(f"\n=== {rac_file} ===")
                    print(result[:500] + "..." if len(result) > 500 else result)
            else:
                skipped += 1
        print(f"\nConverted: {converted}, Skipped: {skipped}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
