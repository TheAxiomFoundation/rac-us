#!/usr/bin/env python3
"""
Compare EITC calculations against PolicyEngine US for 2024.
"""

import sys
from policyengine_us import Simulation


def create_simulation(filing_status, num_children, earned_income, year=2024):
    """
    Create a PolicyEngine simulation for EITC calculation.

    Args:
        filing_status: 'SINGLE' or 'JOINT'
        num_children: Number of qualifying children (0, 1, 2, or 3+)
        earned_income: Total earned income amount
        year: Tax year

    Returns:
        Simulation object
    """
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
                "state_name": {"2024": "NY"},  # Default to NY
            }
        },
    }

    # Add children if specified
    for i in range(num_children):
        child_id = f"child_{i+1}"
        situation["people"][child_id] = {
            "age": {"2024": 5 + i * 3},  # Spread ages: 5, 8, 11
        }
        situation["tax_units"]["tax_unit"]["members"].append(child_id)
        situation["spm_units"]["spm_unit"]["members"].append(child_id)
        situation["households"]["household"]["members"].append(child_id)

    return Simulation(situation=situation)


def calculate_eitc(sim, year=2024):
    """Calculate EITC for the simulation."""
    return sim.calculate("eitc", year)[0]


def run_comparison():
    """Run EITC comparisons for test cases."""

    test_cases = [
        {
            "name": "Single filer, 1 child, $20,000 earned income",
            "filing_status": "SINGLE",
            "num_children": 1,
            "earned_income": 20_000,
            "expected_eitc": 4_213,
            "tolerance": 50,  # Allow $50 tolerance for rounding differences
        },
        {
            "name": "Single filer, 2 children, $30,000 earned income",
            "filing_status": "SINGLE",
            "num_children": 2,
            "earned_income": 30_000,
            "expected_eitc": 5_183,
            "tolerance": 50,
        },
        {
            "name": "Single filer, 0 children, $15,000 earned income",
            "filing_status": "SINGLE",
            "num_children": 0,
            "earned_income": 15_000,
            "expected_eitc": 234,
            "tolerance": 50,
        },
        {
            "name": "Joint filer, 1 child, $25,000 earned income",
            "filing_status": "JOINT",
            "num_children": 1,
            "earned_income": 25_000,
            "expected_eitc": None,  # No expected value provided
            "tolerance": None,
        },
    ]

    print("=" * 80)
    print("EITC COMPARISON: PolicyEngine US vs Expected Values (2024)")
    print("=" * 80)
    print()

    all_passed = True

    for i, test in enumerate(test_cases, 1):
        print(f"Test Case {i}: {test['name']}")
        print("-" * 80)

        # Create simulation
        sim = create_simulation(
            filing_status=test["filing_status"],
            num_children=test["num_children"],
            earned_income=test["earned_income"],
        )

        # Calculate EITC
        calculated_eitc = calculate_eitc(sim)

        # Display results
        print(f"  Filing Status:     {test['filing_status']}")
        print(f"  Number of Children: {test['num_children']}")
        print(f"  Earned Income:     ${test['earned_income']:,}")
        print(f"  Calculated EITC:   ${calculated_eitc:,.2f}")

        if test["expected_eitc"] is not None:
            print(f"  Expected EITC:     ${test['expected_eitc']:,}")
            difference = abs(calculated_eitc - test["expected_eitc"])
            print(f"  Difference:        ${difference:,.2f}")

            if difference <= test["tolerance"]:
                print(f"  Status:            ✓ PASS (within ${test['tolerance']} tolerance)")
            else:
                print(f"  Status:            ✗ FAIL (exceeds ${test['tolerance']} tolerance)")
                all_passed = False
        else:
            print(f"  Expected EITC:     (not specified)")
            print(f"  Status:            INFO (no comparison)")

        print()

    print("=" * 80)
    if all_passed:
        print("RESULT: All tests with expected values PASSED ✓")
    else:
        print("RESULT: Some tests FAILED ✗")
    print("=" * 80)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(run_comparison())
