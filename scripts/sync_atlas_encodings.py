#!/usr/bin/env python3
"""Sync selected rac-us files into public.encoding_runs for Atlas."""

from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
WAVES_DIR = ROOT / "waves"


def iter_manifests(selected_waves: list[str] | None) -> list[tuple[str, dict[str, Any]]]:
    manifests: list[tuple[str, dict[str, Any]]] = []
    if selected_waves:
      wave_dirs = [WAVES_DIR / wave for wave in selected_waves]
    else:
      wave_dirs = sorted(path for path in WAVES_DIR.iterdir() if path.is_dir())

    for wave_dir in wave_dirs:
      manifest_path = wave_dir / "manifest.json"
      if not manifest_path.exists():
          continue
      manifests.append((wave_dir.name, json.loads(manifest_path.read_text())))
    return manifests


def latest_cases(selected_waves: list[str] | None) -> list[dict[str, Any]]:
    cases_by_path: dict[str, dict[str, Any]] = {}
    for wave_name, manifest in iter_manifests(selected_waves):
        for case in manifest.get("cases", []):
            repo_rac_path = case.get("repo_rac_path")
            if not repo_rac_path:
                continue
            cases_by_path[repo_rac_path] = {
                **case,
                "wave": wave_name,
            }
    return [cases_by_path[path] for path in sorted(cases_by_path)]


def is_stub_rac(path: Path) -> bool:
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("status:"):
            return stripped == "status: stub"
    return False


def build_rows(cases: list[dict[str, Any]], include_stubs: bool) -> list[dict[str, Any]]:
    now = datetime.now(UTC).isoformat()
    rows: list[dict[str, Any]] = []
    for case in cases:
        repo_rac_path = case["repo_rac_path"]
        rac_path = ROOT / repo_rac_path
        if not rac_path.exists():
            continue
        if not include_stubs and is_stub_rac(rac_path):
            continue
        rows.append(
            {
                "id": f"rac-us:{repo_rac_path}",
                "timestamp": now,
                "citation": case.get("citation_path", repo_rac_path.removesuffix(".rac")),
                "file_path": repo_rac_path,
                "complexity": {},
                "iterations": [],
                "total_duration_ms": None,
                "predicted_scores": None,
                "final_scores": None,
                "agent_type": "manual-repo",
                "agent_model": None,
                "rac_content": rac_path.read_text(),
                "session_id": None,
                "synced_at": now,
                "data_source": "manual_estimate",
                "has_issues": False,
                "note": f"Imported from rac-us {case['wave']}",
                "autorac_version": None,
            }
        )
    return rows


def chunked(items: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def sync_rows(rows: list[dict[str, Any]], supabase_url: str, service_key: str, batch_size: int) -> None:
    url = supabase_url.rstrip("/") + "/rest/v1/encoding_runs"
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }
    for batch in chunked(rows, batch_size):
        response = requests.post(url, headers=headers, json=batch, timeout=180)
        response.raise_for_status()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wave", action="append", dest="waves", help="Wave directory name to sync; repeatable")
    parser.add_argument("--include-stubs", action="store_true", help="Sync stub RAC files as well as encoded ones")
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    supabase_url = os.environ.get("RAC_SUPABASE_URL")
    service_key = os.environ.get("RAC_SUPABASE_SECRET_KEY")
    if not supabase_url or not service_key:
        raise SystemExit("RAC_SUPABASE_URL and RAC_SUPABASE_SECRET_KEY are required")

    cases = latest_cases(args.waves)
    rows = build_rows(cases, include_stubs=args.include_stubs)
    print(f"Prepared {len(rows)} encoding_runs rows from {len(cases)} manifest cases")

    if args.dry_run:
        if rows:
            print(json.dumps({k: rows[0][k] for k in ["id", "citation", "file_path", "data_source", "note"]}, indent=2))
        return 0

    sync_rows(rows, supabase_url, service_key, args.batch_size)
    print("Synced encoding_runs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
