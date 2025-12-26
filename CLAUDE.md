# cosilico-us

**THE home for US federal tax and benefit statute encodings.**

All US-specific .rac files belong here, NOT in cosilico-engine.

## Structure

Files organized under `statute/` by title and section:

```
cosilico-us/
├── statute/               # All enacted statutes
│   ├── 26/               # Title 26 (IRC)
│   │   ├── 24/          # § 24 - Child Tax Credit
│   │   │   ├── a/credit.rac
│   │   │   ├── b/2/phaseout.rac
│   │   │   └── d/1/B/refundable_credit.rac
│   │   ├── 32/          # § 32 - EITC
│   │   │   ├── a/1/earned_income_credit.rac
│   │   │   └── c/2/A/earned_income.rac
│   │   ├── 62/          # § 62 - AGI
│   │   │   └── a/adjusted_gross_income.rac
│   │   └── 63/          # § 63 - Standard Deduction
│   │       └── c/standard_deduction.rac
│   │
│   └── 7/               # Title 7 (Agriculture)
│       └── 2017/a/      # § 2017(a) - SNAP Allotment
│           └── allotment.rac
│
├── irs/                   # IRS guidance (Rev. Procs, etc.)
│   └── rev-proc-2023-34/
│       └── parameters.yaml
│
└── usda/fns/              # USDA Food & Nutrition Service guidance
    └── snap-fy2024-cola/
        └── parameters.yaml
```

## References in .rac files

Cross-file references use paths relative to the repo root:
```
references {
  earned_income: statute/26/32/c/2/A/earned_income
  agi: statute/26/62/a/adjusted_gross_income
}
```

## File Types

- `.rac` - Executable formulas (compile to Python/JS/WASM)
- `parameters.yaml` - Time-varying values (rates, thresholds, brackets)
- `tests.yaml` - Validation test cases

## Related Repos

- **cosilico-lawarchive** - Source document archive (R2) + catalog
- **cosilico-validators** - Validation against external calculators
- **cosilico-engine** - DSL compiler and runtime
