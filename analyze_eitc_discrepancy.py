#!/usr/bin/env python3
"""
Analyze the EITC discrepancy for Test Case 2.
"""

from policyengine_us import Simulation


def analyze_test_case_2():
    """Analyze the $30k/2 children case in detail."""

    situation = {
        "people": {
            "parent": {
                "age": {"2024": 35},
                "employment_income": {"2024": 30_000},
            },
            "child_1": {
                "age": {"2024": 5},
            },
            "child_2": {
                "age": {"2024": 8},
            },
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
    print("DETAILED EITC ANALYSIS: $30,000 earned income, 2 children")
    print("=" * 80)
    print()

    # Calculate key variables
    print("INCOME COMPONENTS:")
    print(f"  Employment Income:       ${sim.calculate('employment_income', 2024)[0]:,.2f}")
    print(f"  Earned Income:           ${sim.calculate('earned_income', 2024)[0]:,.2f}")
    print(f"  AGI:                     ${sim.calculate('adjusted_gross_income', 2024)[0]:,.2f}")
    print()

    # EITC components
    print("EITC CALCULATION:")
    print(f"  EITC (Total):            ${sim.calculate('eitc', 2024)[0]:,.2f}")

    # Try to get more granular EITC details if available
    try:
        eitc_phased_in = sim.calculate('eitc_phased_in', 2024)[0]
        print(f"  EITC Phased In:          ${eitc_phased_in:,.2f}")
    except:
        print(f"  EITC Phased In:          (not available)")

    try:
        eitc_phased_out = sim.calculate('eitc_phased_out', 2024)[0]
        print(f"  EITC Phased Out:         ${eitc_phased_out:,.2f}")
    except:
        print(f"  EITC Phased Out:         (not available)")

    try:
        eitc_child_count = sim.calculate('eitc_child_count', 2024)[0]
        print(f"  EITC Child Count:        {eitc_child_count}")
    except:
        print(f"  EITC Child Count:        (not available)")

    try:
        eitc_eligible = sim.calculate('eitc_eligible', 2024)[0]
        print(f"  EITC Eligible:           {eitc_eligible}")
    except:
        print(f"  EITC Eligible:           (not available)")

    print()

    # Tax unit details
    print("TAX UNIT DETAILS:")
    print(f"  Filing Status:           {sim.calculate('filing_status', 2024)[0]}")
    print(f"  Tax Unit Size:           {sim.calculate('tax_unit_size', 2024)[0]}")
    print(f"  Tax Unit Dependents:     {sim.calculate('tax_unit_dependents', 2024)[0]}")
    print()

    # Check for state EITC
    print("STATE COMPONENTS:")
    try:
        state_eitc = sim.calculate('ny_eitc', 2024)[0]
        print(f"  NY State EITC:           ${state_eitc:,.2f}")
    except:
        print(f"  NY State EITC:           (not available)")
    print()

    print("=" * 80)
    print("EXPECTED vs CALCULATED:")
    print(f"  Expected EITC:           $5,183.00")
    print(f"  Calculated EITC:         ${sim.calculate('eitc', 2024)[0]:,.2f}")
    print(f"  Difference:              ${abs(sim.calculate('eitc', 2024)[0] - 5183):,.2f}")
    print("=" * 80)
    print()

    # Manual EITC calculation for 2024 with 2 children
    print("MANUAL EITC CALCULATION (2024 parameters):")
    print("  For 2 children:")
    print("    - Phase-in rate: 40%")
    print("    - Phase-in max: $15,410")
    print("    - Maximum credit: $6,164")
    print("    - Phase-out threshold (Single): $19,520")
    print("    - Phase-out rate: 21.06%")
    print()

    earned = 30_000
    phase_in_rate = 0.40
    phase_in_max = 15_410
    max_credit = 6_164
    phase_out_threshold = 19_520
    phase_out_rate = 0.2106

    # Calculate phase-in amount
    phase_in_amount = min(earned * phase_in_rate, max_credit)
    print(f"  Phase-in amount: min(${earned:,} * {phase_in_rate}, ${max_credit:,}) = ${phase_in_amount:,.2f}")

    # Calculate phase-out reduction
    if earned > phase_out_threshold:
        excess = earned - phase_out_threshold
        phase_out_reduction = excess * phase_out_rate
        print(f"  Phase-out reduction: (${earned:,} - ${phase_out_threshold:,}) * {phase_out_rate} = ${phase_out_reduction:,.2f}")
    else:
        phase_out_reduction = 0
        print(f"  Phase-out reduction: $0 (income below threshold)")

    manual_eitc = max(0, phase_in_amount - phase_out_reduction)
    print(f"  Manual EITC: ${manual_eitc:,.2f}")
    print()

    print("This suggests the expected value of $5,183 may be outdated or from a different year.")


if __name__ == "__main__":
    analyze_test_case_2()
