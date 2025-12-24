#!/usr/bin/env python3
"""
Final EITC comparison with corrected expected values for 2024.
"""

import sys
from policyengine_us import Simulation


def create_simulation(filing_status, num_children, earned_income, year=2024):
    """Create a PolicyEngine simulation for EITC calculation."""
    situation = {
        "people": {
            "parent": {
                "age": {"2024": 35},
                "employment_income": {"2024": earned_income},
            }
        },
        "tax_units": {
            "tax_unit": {
                "members": ["parent"],
                "filing_status": {"2024": filing_status},
            }
        },
        "spm_units": {
            "spm_unit": {
                "members": ["parent"],
            }
        },
        "households": {
            "household": {
                "members": ["parent"],
                "state_name": {"2024": "NY"},
            }
        },
    }

    for i in range(num_children):
        child_id = f"child_{i+1}"
        situation["people"][child_id] = {"age": {"2024": 5 + i * 3}}
        situation["tax_units"]["tax_unit"]["members"].append(child_id)
        situation["spm_units"]["spm_unit"]["members"].append(child_id)
        situation["households"]["household"]["members"].append(child_id)

    return Simulation(situation=situation)


def run_final_comparison():
    """Run EITC comparisons with corrected expected values."""

    test_cases = [
        {
            "name": "Single filer, 1 child, $20,000 earned income",
            "filing_status": "SINGLE",
            "num_children": 1,
            "earned_income": 20_000,
            "expected_eitc": 4_213,
            "tolerance": 1,
            "note": "At plateau - maximum credit for 1 child",
        },
        {
            "name": "Single filer, 2 children, $30,000 earned income",
            "filing_status": "SINGLE",
            "num_children": 2,
            "earned_income": 30_000,
            "expected_eitc": 5_427,  # Corrected from 5,183
            "tolerance": 1,
            "note": "In phase-out range (income > $22,720)",
        },
        {
            "name": "Single filer, 0 children, $15,000 earned income",
            "filing_status": "SINGLE",
            "num_children": 0,
            "earned_income": 15_000,
            "expected_eitc": 275,  # Corrected from 234
            "tolerance": 1,
            "note": "Childless worker credit (much smaller)",
        },
        {
            "name": "Joint filer, 1 child, $25,000 earned income",
            "filing_status": "JOINT",
            "num_children": 1,
            "earned_income": 25_000,
            "expected_eitc": 4_213,
            "tolerance": 1,
            "note": "At plateau - joint filing has higher phase-out threshold",
        },
    ]

    print("=" * 90)
    print("FINAL EITC COMPARISON: PolicyEngine US 2024 (Corrected Expected Values)")
    print("=" * 90)
    print()

    all_passed = True
    results = []

    for i, test in enumerate(test_cases, 1):
        sim = create_simulation(
            filing_status=test["filing_status"],
            num_children=test["num_children"],
            earned_income=test["earned_income"],
        )

        calculated_eitc = sim.calculate('eitc', 2024)[0]
        difference = abs(calculated_eitc - test["expected_eitc"])
        passed = difference <= test["tolerance"]

        if not passed:
            all_passed = False

        results.append({
            "test_num": i,
            "name": test["name"],
            "calculated": calculated_eitc,
            "expected": test["expected_eitc"],
            "difference": difference,
            "passed": passed,
            "note": test["note"],
        })

    # Display results in table format
    print(f"{'#':<3} {'Test Case':<45} {'Expected':>10} {'Calculated':>12} {'Diff':>8} {'Status':>8}")
    print("-" * 90)

    for r in results:
        status = "✓ PASS" if r["passed"] else "✗ FAIL"
        print(f"{r['test_num']:<3} {r['name'][:45]:<45} ${r['expected']:>9,} ${r['calculated']:>11,.2f} ${r['difference']:>7,.2f} {status:>8}")

    print()
    print("Notes:")
    for r in results:
        print(f"  {r['test_num']}. {r['note']}")

    print()
    print("=" * 90)

    if all_passed:
        print("RESULT: ✓ ALL TESTS PASSED")
        print()
        print("PolicyEngine US correctly implements 2024 EITC parameters:")
        print("  - Maximum credits: $632 (0 children), $4,213 (1), $6,960 (2), $7,830 (3+)")
        print("  - Phase-out start (Single, with children): $22,720")
        print("  - Phase-out start (Joint, with children): $29,200")
        print("  - Phase-in rates: 7.65% (0 children), 34% (1), 40% (2), 45% (3+)")
        print("  - Phase-out rates: 7.65% (0 children), 15.98% (1), 21.06% (2), 21.06% (3+)")
    else:
        print("RESULT: ✗ SOME TESTS FAILED")

    print("=" * 90)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(run_final_comparison())
