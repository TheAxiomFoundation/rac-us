from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
STATUTES_ROOT = ROOT / "statutes"
IGNORED_DIRS = {".git", ".pytest_cache", ".venv", "__pycache__", "_axiom"}


def iter_repo_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.relative_to(ROOT).parts):
            continue
        if path.is_file():
            files.append(path)
    return sorted(files)


def iter_rulespec_files() -> list[Path]:
    return sorted(
        path
        for path in STATUTES_ROOT.rglob("*.yaml")
        if not path.name.endswith(".test.yaml")
    )


def test_no_obsolete_formula_artifacts() -> None:
    obsolete = [
        path.relative_to(ROOT).as_posix()
        for path in iter_repo_files()
        if path.name.endswith(".rac") or path.name.endswith(".rac.test")
    ]

    assert obsolete == []


def test_statute_rulespec_files_have_companion_tests() -> None:
    missing = [
        path.relative_to(ROOT).as_posix()
        for path in iter_rulespec_files()
        if not path.with_name(f"{path.stem}.test.yaml").exists()
    ]

    assert missing == []


def test_companion_tests_have_rulespec_files() -> None:
    orphaned = [
        path.relative_to(ROOT).as_posix()
        for path in sorted(STATUTES_ROOT.rglob("*.test.yaml"))
        if not path.with_name(f"{path.stem.removesuffix('.test')}.yaml").exists()
    ]

    assert orphaned == []


def test_statute_rulespec_files_use_rulespec_v1_shape() -> None:
    invalid: list[str] = []

    for path in iter_rulespec_files():
        payload = yaml.safe_load(path.read_text()) or {}
        if not isinstance(payload, dict):
            invalid.append(f"{path.relative_to(ROOT)}: top-level YAML is not a mapping")
            continue
        if payload.get("format") != "rulespec/v1":
            invalid.append(f"{path.relative_to(ROOT)}: missing format: rulespec/v1")
        rules = payload.get("rules")
        if not isinstance(rules, list) or not rules:
            invalid.append(f"{path.relative_to(ROOT)}: missing non-empty rules list")
            continue
        for index, rule in enumerate(rules):
            if not isinstance(rule, dict):
                invalid.append(f"{path.relative_to(ROOT)}: rules[{index}] is not a mapping")
                continue
            for key in ("name", "kind", "versions"):
                if key not in rule:
                    invalid.append(f"{path.relative_to(ROOT)}: rules[{index}] missing {key}")

    assert invalid == []
