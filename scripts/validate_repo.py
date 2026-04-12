from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import repo_layout


ROOT = Path(__file__).resolve().parents[1]
CONTENT_ROOT = repo_layout.content_root(ROOT)
LOCAL_RAC_ROOT = ROOT.parent / "rac"


def run_step(name: str, command: list[str], cwd: Path | None = None) -> None:
    print(f"==> {name}")
    result = subprocess.run(command, cwd=cwd or ROOT)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def rac_validate_invocation() -> tuple[list[str], Path | None]:
    if importlib.util.find_spec("rac") is not None:
        return [sys.executable, "-m", "rac.validate"], ROOT
    if shutil.which("uv") and LOCAL_RAC_ROOT.exists():
        return ["uv", "run", "python", "-m", "rac.validate"], LOCAL_RAC_ROOT
    if shutil.which("uv"):
        return ["uv", "run", "python", "-m", "rac.validate"], ROOT
    return [sys.executable, "-m", "rac.validate"], ROOT


def main() -> int:
    validate_cmd, validate_cwd = rac_validate_invocation()
    run_step(
        "Validate .rac schema and imports",
        [*validate_cmd, "all", str(CONTENT_ROOT)],
        cwd=validate_cwd,
    )
    run_step(
        "Check manual-wave policy",
        [sys.executable, str(ROOT / "scripts" / "check_manual_wave_policy.py")],
    )
    run_step(
        "Check companion .rac.test coverage against the tracked baseline",
        [sys.executable, str(ROOT / "scripts" / "check_companion_tests.py")],
    )
    run_step(
        "Check for embedded scalar literals against the tracked baseline",
        [sys.executable, str(ROOT / "scripts" / "check_embedded_scalars.py")],
    )
    run_step(
        "Check source-number coverage against the tracked baseline",
        [sys.executable, str(ROOT / "scripts" / "check_numeric_occurrence_coverage.py")],
    )
    print("All rac-us validation checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
