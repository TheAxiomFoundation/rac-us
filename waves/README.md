# US Wave Provenance

`rac-us` wave provenance lives under `waves/`.

This directory serves two purposes:

- durable provenance for future US promotions
- honest backfills for the historical US batch commits that predate this pattern

## Tiers

- `full`
  Use for new US promotions going forward. These should include the real `autorac`
  provenance when it exists: benchmark manifest, suite results path, `autorac`
  commit/version, runner, and any eval run roots that seeded the promotion.

- `backfilled_git_history`
  Use when we only know the `rac-us` commit that introduced a batch. These
  manifests are still useful because they pin the promoted files and the exact
  repo commit/date, but they do not pretend to know missing `autorac` metadata.

- `manual_repo_change`
  Use for tracked manual cleanups or refactors that materially change promoted
  `.rac` files without being a fresh `autorac` generation wave.

## Policy

- Every future nontrivial US promotion should commit a manifest under
  `waves/<date>-waveN/manifest.json` in the same change that lands the `.rac`
  files.
- If the source is an `autorac` run, record the exact `autorac` commit, version,
  runner, and run roots while they still exist.
- If the change is manual, say so explicitly rather than inventing generation
  provenance.

## Helper

Use the helper script to scaffold a manifest from a `rac-us` commit:

```bash
python scripts/create_wave_manifest.py \
  --wave 2026-04-02-wave7 \
  --source-commit HEAD \
  --provenance-tier full \
  --change-kind encoding \
  --autorac-commit <commit> \
  --autorac-version <version> \
  --runner openai-gpt-5.4 \
  --suite-manifest /abs/path/to/benchmark.yaml \
  --suite-results-json /abs/path/to/results.json \
  --source-eval-run /abs/path/to/run-root \
  --write
```
