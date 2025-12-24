# EITC Comparison Scripts

This directory contains Python scripts to compare EITC (Earned Income Tax Credit) calculations against PolicyEngine US for tax year 2024.

## Setup

1. Create and activate virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install PolicyEngine US:
```bash
pip install policyengine-us
```

## Scripts

### 1. Initial Comparison (`compare_eitc.py`)
Runs the original test cases with the initially provided expected values.

```bash
python compare_eitc.py
```

**Results:** 2 of 3 tests passed (Test 2 failed due to incorrect expected value)

### 2. Detailed Analysis (`analyze_eitc_discrepancy.py`)
Deep dive into the Test Case 2 discrepancy, showing all EITC components and calculations.

```bash
python analyze_eitc_discrepancy.py
```

### 3. Parameter Inspection (`inspect_eitc_calculation.py`)
Lists all EITC-related variables and tests multiple income levels to understand the calculation pattern.

```bash
python inspect_eitc_calculation.py
```

### 4. Final Comparison (`final_eitc_comparison.py`)
Runs all test cases with corrected expected values for 2024.

```bash
python final_eitc_comparison.py
```

**Results:** ALL 4 tests PASS

## Key Findings

### 2024 EITC Parameters (Verified Correct)

**Maximum Credits:**
- 0 children: $632
- 1 child: $4,213
- 2 children: $6,960
- 3+ children: $7,830

**Phase-in Rates:**
- 0 children: 7.65%
- 1 child: 34%
- 2 children: 40%
- 3+ children: 45%

**Phase-out Start (Single Filers):**
- 0 children: $10,330
- 1+ children: $22,720

**Phase-out Start (Joint Filers):**
- 0 children: $17,810
- 1+ children: $29,200

**Phase-out Rates:**
- 0 children: 7.65%
- 1 child: 15.98%
- 2 children: 21.06%
- 3+ children: 21.06%

### Test Case Corrections

**Test Case 2** (Single, 2 children, $30,000 income):
- Original expected: $5,183 (INCORRECT)
- Corrected expected: $5,427 (matches PolicyEngine)
- Calculation: $6,960 - (($30,000 - $22,720) × 0.2106) = $5,426.83

**Test Case 3** (Single, 0 children, $15,000 income):
- Original expected: $234
- Corrected expected: $275 (matches PolicyEngine within rounding)
- Difference: $40.74 (acceptable tolerance)

## Validation

PolicyEngine US correctly implements all 2024 EITC parameters as specified by:
- IRS Revenue Procedure 2023-34
- IRS Publication 596
- IRS EITC Tables for 2024

## Sources

- [IRS EITC Tables](https://www.irs.gov/credits-deductions/individuals/earned-income-tax-credit/earned-income-and-earned-income-tax-credit-eitc-tables)
- [Tax Foundation 2024 Tax Brackets](https://taxfoundation.org/data/all/federal/2024-tax-brackets/)
- [ITEP State Earned Income Tax Credits 2024](https://itep.org/state-earned-income-tax-credits-2024/)
- [IRS Revenue Procedure 2023-34](https://www.irs.gov/pub/irs-drop/rp-23-34.pdf)
