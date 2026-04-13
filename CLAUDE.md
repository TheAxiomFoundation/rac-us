# rac-us

**THE home for US federal tax and benefit statute encodings.**

Federal U.S. cores belong here. State-administered overlays belong in their
jurisdiction repos, not in `rac-us` and not in `rac-compile`.

## Structure

Files organized under `statute/` by title and section:

```
rac-us/
├── statute/               # All enacted statutes
│   ├── 26/               # Title 26 (IRC)
│   │   ├── 24/          # § 24 - Child Tax Credit
│   │   ├── 32/          # § 32 - EITC
│   │   ├── 36B/         # § 36B - Premium Tax Credit
│   │   └── ...
│   └── 7/               # Title 7 (Agriculture)
│       ├── 2014/        # § 2014 - SNAP Eligibility
│       └── 2017/        # § 2017 - SNAP Allotment
```

## Filepath = citation

```
statute/26/32/c/2/A.rac  →  26 USC § 32(c)(2)(A)
statute/7/2017/a.rac     →  7 USC § 2017(a)
```

## .rac format

See `rac/docs/RAC_SPEC.md` for full specification. Key features:

**No keyword prefixes** — type inferred from fields:
```yaml
# Parameter (no entity field)
contribution_rate:
  description: "Household contribution as share of net income"
  from 1977-01-01: 0.30

# Computed value (has entity field)
snap_allotment:
  imports:
    - 7/2014#household_size
  entity: Household
  period: Month
  dtype: Money
  from 2024-01-01:
    if not snap_eligible: 0
    else: max_allotment - net_income * contribution_rate
```

**Expression-based formulas** — the last expression is the value. No `return` keyword.

**Self-contained**: statute text, parameters, computed values, and tests in one file.

**Import syntax**: `path#variable` or `path#variable as alias`

**Scoping**:
- Parameters: in scope for all variables in file
- Same-file variables: in scope for later variables (dependency order)
- Imports: in scope for that variable's formula only

## Formula rules

**Allowed literals**: only -1, 0, 1, 2, 3

```python
# BAD - hardcoded values
if age >= 65: ...
threshold = income * 0.075

# GOOD - parameterized
if age >= elderly_age_threshold: ...
threshold = income * medical_expense_threshold_rate
```

## Commands

```bash
# Create a wave provenance manifest from a rac-us commit
python scripts/create_wave_manifest.py --wave 2026-04-02-wave7 --source-commit HEAD --write

# Run the full repo validation suite (schema/imports + baseline-aware audits)
python scripts/validate_repo.py

# Validate all .rac files (schema + imports)
python -m rac.validate all statute/

# Validate schema only
python -m rac.validate schema statute/

# Validate imports only
python -m rac.validate imports statute/

# Run inline tests
python -m rac.test_runner statute/ -v

# Report tracked backlog for newer audits
python scripts/report_missing_companion_tests.py
python scripts/report_embedded_scalars.py
python scripts/report_numeric_occurrence_coverage.py
```

## Related repos

- **rac** - DSL parser, compiler, and runtime
- **atlas** - Source document archive
- **autorac** - AI-assisted statute encoding
- **rac-validators** - Validation against external calculators

## Wave provenance

Wave-level provenance for `rac-us` lives under [waves](/Users/maxghenis/TheAxiomFoundation/rac-us/waves).

Current tracked waves:

- `2026-03-07-wave1`: clean-slate re-encode touching section 21 and section 24(d), backfilled from git history
- `2026-03-08-wave2`: external dependency and supporting-definition batch, backfilled from git history
- `2026-03-09-wave3`: major 26 USC 32 (EITC) batch, backfilled from git history
- `2026-03-09-wave4`: major 26 USC 63 taxable-income batch, backfilled from git history
- `2026-03-09-wave5`: major 26 USC 24 (CTC) batch, backfilled from git history
- `2026-04-02-wave6`: manual demo-facing US tax-credit cleanup and provenance hardening

- Historical US batch commits are backfilled as `backfilled_git_history` manifests.
- New promotions should record full `autorac` provenance at promotion time.
- Direct manual promotion of `.rac` policy changes is forbidden. New changes to
  promoted `.rac` files must come through AutoRAC-generated runs and full
  AutoRAC provenance, not `manual_repo_change`.
