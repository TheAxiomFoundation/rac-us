from __future__ import annotations

from pathlib import Path


CONTENT_DIR_CANDIDATES = ("statutes",)


def content_root(root: Path) -> Path:
    for name in CONTENT_DIR_CANDIDATES:
        candidate = root / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"Could not find repo content root under {root} "
        f"(expected one of: {', '.join(CONTENT_DIR_CANDIDATES)})."
    )
