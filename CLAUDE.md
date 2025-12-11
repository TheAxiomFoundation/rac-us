# cosilico-us

Executable encodings of US federal tax and benefit law in Cosilico DSL.

## Structure

Files organized by source document type and citation path:

```
cosilico-us/
├── 26/                    # Title 26 (IRC) statutes
│   ├── 24/               # § 24 - Child Tax Credit
│   │   ├── a/credit.cosilico
│   │   ├── b/1/threshold.yaml
│   │   └── h/2/credit_amount.yaml
│   └── 63/               # § 63 - Standard Deduction
│       └── c/standard_deduction.cosilico
│
├── 7/                     # Title 7 (Agriculture) statutes
│   └── 2017/a/           # § 2017(a) - SNAP Allotment
│       └── allotment.cosilico
│
├── irs/                   # IRS guidance (Rev. Procs, etc.)
│   └── rev-proc-2023-34/
│       └── parameters.yaml
│
└── usda/fns/              # USDA Food & Nutrition Service guidance
    └── snap-fy2024-cola/
        └── parameters.yaml
```

## File Types

- `.cosilico` - Executable formulas (compile to Python/JS/WASM)
- `parameters.yaml` - Time-varying values (rates, thresholds, brackets)
- `tests.yaml` - Validation test cases

## Related Repos

- **cosilico-lawarchive** - Source document archive (R2) + catalog
- **cosilico-validators** - Validation against external calculators
- **cosilico-engine** - DSL compiler and runtime
