#!/usr/bin/env python3
"""
Check the actual EITC parameters used by PolicyEngine US for 2024.
"""

from policyengine_us import Simulation
from policyengine_core.parameters import ParameterNode


def check_eitc_parameters():
    """Check EITC parameters for 2024."""

    # Create a minimal simulation to access parameters
    situation = {
        "people": {"person": {"age": {"2024": 30}}},
        "tax_units": {
            "tax_unit": {
                "members": ["person"],
                "filing_status": {"2024": "SINGLE"},
            }
        },
        "spm_units": {"spm_unit": {"members": ["person"]}},
        "households": {
            "household": {
                "members": ["person"],
                "state_name": {"2024": "NY"},
            }
        },
    }

    sim = Simulation(situation=situation)
    params = sim.tax_benefit_system.parameters

    print("=" * 80)
    print("EITC PARAMETERS FOR 2024")
    print("=" * 80)
    print()

    # Navigate to EITC parameters
    try:
        eitc_params = params("2024-01-01").gov.irs.credits.eitc

        print("MAXIMUM CREDIT BY NUMBER OF CHILDREN:")
        for i in range(4):
            try:
                max_credit = eitc_params.max[i]("2024-01-01")
                print(f"  {i} child(ren): ${max_credit:,.2f}")
            except:
                pass
        print()

        print("PHASE-IN RATE BY NUMBER OF CHILDREN:")
        for i in range(4):
            try:
                phase_in = eitc_params.phase_in_rate[i]("2024-01-01")
                print(f"  {i} child(ren): {phase_in:.2%}")
            except:
                pass
        print()

        print("PHASE-OUT RATE BY NUMBER OF CHILDREN:")
        for i in range(4):
            try:
                phase_out = eitc_params.phase_out_rate[i]("2024-01-01")
                print(f"  {i} child(ren): {phase_out:.4%}")
            except:
                pass
        print()

        print("PHASE-OUT START (SINGLE):")
        for i in range(4):
            try:
                threshold = eitc_params.phase_out_start.SINGLE[i]("2024-01-01")
                print(f"  {i} child(ren): ${threshold:,.2f}")
            except:
                pass
        print()

        print("PHASE-OUT START (JOINT):")
        for i in range(4):
            try:
                threshold = eitc_params.phase_out_start.JOINT[i]("2024-01-01")
                print(f"  {i} child(ren): ${threshold:,.2f}")
            except:
                pass
        print()

        print("PHASE-IN PLATEAU (Maximum earned income for full credit):")
        for i in range(4):
            try:
                plateau = eitc_params.max[i]("2024-01-01") / eitc_params.phase_in_rate[i]("2024-01-01")
                print(f"  {i} child(ren): ${plateau:,.2f}")
            except:
                pass
        print()

    except Exception as e:
        print(f"Error accessing EITC parameters: {e}")
        print()

    # Now let's verify with a specific calculation
    print("=" * 80)
    print("VERIFICATION: $30,000 earned income, 2 children, Single")
    print("=" * 80)
    print()

    situation2 = {
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

    sim2 = Simulation(situation=situation2)

    # Get parameters for 2 children
    max_credit = eitc_params.max[2]("2024-01-01")
    phase_in_rate = eitc_params.phase_in_rate[2]("2024-01-01")
    phase_out_rate = eitc_params.phase_out_rate[2]("2024-01-01")
    phase_out_start = eitc_params.phase_out_start.SINGLE[2]("2024-01-01")

    earned = 30_000

    print(f"Parameters used:")
    print(f"  Max credit: ${max_credit:,.2f}")
    print(f"  Phase-in rate: {phase_in_rate:.2%}")
    print(f"  Phase-out rate: {phase_out_rate:.4%}")
    print(f"  Phase-out start: ${phase_out_start:,.2f}")
    print()

    # Phase-in calculation
    phase_in_plateau = max_credit / phase_in_rate
    if earned <= phase_in_plateau:
        credit_phased_in = earned * phase_in_rate
    else:
        credit_phased_in = max_credit

    print(f"Phase-in plateau: ${phase_in_plateau:,.2f}")
    print(f"Credit after phase-in: ${credit_phased_in:,.2f}")
    print()

    # Phase-out calculation
    if earned > phase_out_start:
        excess = earned - phase_out_start
        phase_out_reduction = excess * phase_out_rate
        final_credit = max(0, credit_phased_in - phase_out_reduction)
    else:
        phase_out_reduction = 0
        final_credit = credit_phased_in

    print(f"Excess over phase-out start: ${max(0, earned - phase_out_start):,.2f}")
    print(f"Phase-out reduction: ${phase_out_reduction:,.2f}")
    print(f"Final credit (manual): ${final_credit:,.2f}")
    print()

    actual_eitc = sim2.calculate('eitc', 2024)[0]
    print(f"Actual EITC (PolicyEngine): ${actual_eitc:,.2f}")
    print(f"Difference: ${abs(final_credit - actual_eitc):,.2f}")


if __name__ == "__main__":
    check_eitc_parameters()
