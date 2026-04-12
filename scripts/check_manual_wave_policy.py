from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WAVES_ROOT = ROOT / "waves"

# Historical/manual exceptions already present in repo history. New waves must not use
# manual provenance; the system should promote via AutoRAC-generated evidence.
ALLOWED_MANUAL_WAVES = {
    "2026-04-02-wave6",
    "2026-04-02-wave7",
    "2026-04-11-wave8",
    "2026-04-11-wave9",
    "2026-04-11-wave10",
    "2026-04-11-wave11",
    "2026-04-11-wave12",
    "2026-04-11-wave13",
    "2026-04-11-wave14",
    "2026-04-11-wave15",
    "2026-04-11-wave16",
    "2026-04-11-wave17",
    "2026-04-11-wave18",
    "2026-04-11-wave19",
    "2026-04-11-wave20",
    "2026-04-11-wave21",
    "2026-04-11-wave22",
}


def main() -> int:
    offending: list[tuple[str, str]] = []
    for manifest_path in sorted(WAVES_ROOT.glob("*/manifest.json")):
        payload = json.loads(manifest_path.read_text())
        wave = str(payload.get("wave", manifest_path.parent.name))
        tier = str(payload.get("provenance_tier", ""))
        if tier == "manual_repo_change" and wave not in ALLOWED_MANUAL_WAVES:
            offending.append((wave, manifest_path.relative_to(ROOT).as_posix()))

    if offending:
        print(
            "Manual provenance waves are forbidden for new rac-us promotions. "
            "Use AutoRAC-generated provenance instead.",
            file=sys.stderr,
        )
        for wave, rel_path in offending:
            print(f"- {wave}: {rel_path}", file=sys.stderr)
        return 1

    print("Manual wave policy check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
