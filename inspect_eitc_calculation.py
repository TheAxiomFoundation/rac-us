#!/usr/bin/env python3
"""
Inspect how PolicyEngine calculates EITC to understand the discrepancy.
"""

from policyengine_us import Simulation
import json


def inspect_eitc():
    """Inspect EITC calculation details."""

    # Test case: $30k, 2 children
    situation = {
        "people": {
            "parent": {
                "age": {"2024": 35},
                "employment_income": {"2024": 30_000},
            },
            "child_1": {"age": {"2024": 5}},
            "child_2": {"age": {"2024": 8}},
        },
        "tax_units": {
            "tax_unit": {
                "members": ["parent", "child_1", "child_2"],
                "filing_status": {"2024": "SINGLE"},
            }
        },
        "spm_units": {
            "spm_unit": {
                "members": ["parent", "child_1", "child_2"],
            }
        },
        "households": {
            "household": {
                "members": ["parent", "child_1", "child_2"],
                "state_name": {"2024": "NY"},
            }
        },
    }

    sim = Simulation(situation=situation)

    print("=" * 80)
    print("INSPECTING EITC CALCULATION")
    print("=" * 80)
    print()

    # List all variables that contain "eitc" in the name
    print("EITC-related variables:")
    variables = [v for v in sim.tax_benefit_system.variables if "eitc" in v.lower()]
    for var in sorted(variables):
        try:
            value = sim.calculate(var, 2024)[0]
            if value != 0 and value is not None and value != False:
                print(f"  {var}: {value}")
        except:
            pass
    print()

    # Key income variables
    print("INCOME VARIABLES:")
    income_vars = [
        "employment_income",
        "earned_income",
        "adjusted_gross_income",
        "taxable_income",
    ]
    for var in income_vars:
        try:
            value = sim.calculate(var, 2024)[0]
            print(f"  {var}: ${value:,.2f}")
        except Exception as e:
            print(f"  {var}: Error - {e}")
    print()

    # Try different test cases to understand the pattern
    print("=" * 80)
    print("TESTING MULTIPLE INCOME LEVELS (2 children, Single)")
    print("=" * 80)
    print()

    test_incomes = [10_000, 15_000, 20_000, 25_000, 30_000, 35_000, 40_000]

    print(f"{'Income':>10} | {'EITC':>10} | {'Effective Rate':>15}")
    print("-" * 42)

    for income in test_incomes:
        test_situation = {
            "people": {
                "parent": {
                    "age": {"2024": 35},
                    "employment_income": {"2024": income},
                },
                "child_1": {"age": {"2024": 5}},
                "child_2": {"age": {"2024": 8}},
            },
            "tax_units": {
                "tax_unit": {
                    "members": ["parent", "child_1", "child_2"],
                    "filing_status": {"2024": "SINGLE"},
                }
            },
            "spm_units": {
                "spm_unit": {
                    "members": ["parent", "child_1", "child_2"],
                }
            },
            "households": {
                "household": {
                    "members": ["parent", "child_1", "child_2"],
                    "state_name": {"2024": "NY"},
                }
            },
        }

        test_sim = Simulation(situation=test_situation)
        eitc = test_sim.calculate('eitc', 2024)[0]
        rate = (eitc / income * 100) if income > 0 else 0

        print(f"${income:>9,} | ${eitc:>9,.2f} | {rate:>13.2f}%")

    print()
    print("=" * 80)
    print("IRS 2024 EITC TABLE (for comparison)")
    print("=" * 80)
    print()
    print("According to IRS.gov for 2024:")
    print("  2 children, Single filer:")
    print("    - Maximum credit: $6,960")
    print("    - Phase-in rate: 40%")
    print("    - Plateau income: $17,400")
    print("    - Phase-out start: $20,330")
    print("    - Phase-out rate: 21.06%")
    print("    - Phase-out end: $53,120")
    print()

    # Manual calculation with 2024 IRS parameters
    earned = 30_000
    max_credit = 6_960
    phase_in_rate = 0.40
    plateau = 17_400
    phase_out_start = 20_330
    phase_out_rate = 0.2106

    if earned <= plateau:
        credit = earned * phase_in_rate
    else:
        credit = max_credit

    if earned > phase_out_start:
        excess = earned - phase_out_start
        reduction = excess * phase_out_rate
        credit = max(0, credit - reduction)

    print(f"Manual calculation for $30,000:")
    print(f"  Phase-in: ${min(earned * phase_in_rate, max_credit):,.2f}")
    print(f"  Phase-out reduction: ${(earned - phase_out_start) * phase_out_rate:,.2f}")
    print(f"  Final EITC: ${credit:,.2f}")
    print()
    print(f"PolicyEngine calculated: ${sim.calculate('eitc', 2024)[0]:,.2f}")
    print(f"Difference: ${abs(credit - sim.calculate('eitc', 2024)[0]):,.2f}")


if __name__ == "__main__":
    inspect_eitc()
