#!/usr/bin/env python3
"""
Validation script for 26 USC 1 encoding against PolicyEngine US
Compares our RAC encoding results with PolicyEngine calculations
"""

import yaml
import pandas as pd
from policyengine_us import Simulation
import json

# Load test cases
with open('/Users/maxghenis/CosilicoAI/rac-us/statute/26/1/tests.yaml', 'r') as f:
    test_data = yaml.safe_load(f)

# Map our filing status names to PolicyEngine
FILING_STATUS_MAP = {
    'SINGLE': 'SINGLE',
    'MARRIED_FILING_JOINTLY': 'JOINT',
    'HEAD_OF_HOUSEHOLD': 'HEAD_OF_HOUSEHOLD',
    'MARRIED_FILING_SEPARATELY': 'SEPARATE',
    'ESTATE_TRUST': 'SINGLE'  # PE doesn't have estate/trust, use single as proxy
}

def create_pe_situation(test_case):
    """Create PolicyEngine situation from test case inputs.

    For validating 26 USC 1 (tax rate schedules), we set taxable_income
    directly to test the rate calculation in isolation.
    """
    inputs = test_case['inputs']

    # Map filing status
    filing_status = FILING_STATUS_MAP.get(inputs['filing_status'], 'SINGLE')

    # Create basic situation
    year = inputs['tax_year']
    situation = {
        "people": {
            "adult": {
                "age": {year: inputs.get('age', 40)},  # Age 40 to avoid age-based credits
            }
        },
        "tax_units": {
            "tu": {
                "members": ["adult"],
                "filing_status": {year: filing_status},
                # Set taxable_income directly to test rate schedules in isolation
                "taxable_income": {year: inputs['taxable_income']},
            }
        },
        "households": {
            "hh": {
                "members": ["adult"],
                "state_code": {year: "TX"}  # Use Texas (no state tax)
            }
        }
    }

    # Add capital gains if specified (for testing capital gains rates)
    if 'net_capital_gain' in inputs:
        situation["people"]["adult"]["long_term_capital_gains"] = {year: inputs['net_capital_gain']}

    return situation

def run_validation():
    """Run validation against PolicyEngine"""
    results = []

    for i, test_case in enumerate(test_data['test_cases']):
        print(f"Running test {i+1}/{len(test_data['test_cases'])}: {test_case['name']}")

        try:
            # Create PolicyEngine situation
            situation = create_pe_situation(test_case)

            # Run simulation
            sim = Simulation(situation=situation)
            year = test_case['inputs']['tax_year']

            # Get income tax before refundable credits from PolicyEngine
            # This isolates the tax rate schedule calculation (26 USC 1)
            # calculate() returns numpy array, get first (only) tax unit's value
            pe_income_tax = float(sim.calculate("income_tax_before_refundable_credits", year)[0])

            # Our expected value
            expected = test_case['expected']['income_tax']

            # Calculate match
            matches = abs(pe_income_tax - expected) < 1.0  # $1 tolerance
            percent_diff = ((pe_income_tax - expected) / max(expected, 1)) * 100 if expected > 0 else 0

            result = {
                'test_name': test_case['name'],
                'taxable_income': test_case['inputs']['taxable_income'],
                'filing_status': test_case['inputs']['filing_status'],
                'tax_year': test_case['inputs']['tax_year'],
                'expected_tax': expected,
                'policyengine_tax': float(pe_income_tax),
                'difference': float(pe_income_tax - expected),
                'percent_difference': percent_diff,
                'matches': matches,
                'reference': test_case['reference']
            }

            results.append(result)

            # Print immediate feedback
            if matches:
                print(f"  ✅ MATCH: Expected {expected:,.0f}, PE {pe_income_tax:,.0f}")
            else:
                print(f"  ❌ DIFF: Expected {expected:,.0f}, PE {pe_income_tax:,.0f} (diff: {pe_income_tax - expected:+,.0f})")

        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            result = {
                'test_name': test_case['name'],
                'taxable_income': test_case['inputs']['taxable_income'],
                'filing_status': test_case['inputs']['filing_status'],
                'tax_year': test_case['inputs']['tax_year'],
                'expected_tax': test_case['expected']['income_tax'],
                'policyengine_tax': None,
                'difference': None,
                'percent_difference': None,
                'matches': False,
                'reference': test_case['reference'],
                'error': str(e)
            }
            results.append(result)

    return pd.DataFrame(results)

def generate_report(df):
    """Generate validation report"""
    total_tests = len(df)
    matches = df['matches'].sum()
    match_rate = (matches / total_tests) * 100

    # Aggregate comparison
    total_expected = df['expected_tax'].sum()
    total_pe = df['policyengine_tax'].sum()
    aggregate_diff_pct = ((total_pe - total_expected) / total_expected) * 100 if total_expected > 0 else 0

    print("\n" + "="*80)
    print("VALIDATION REPORT: 26 USC 1 vs PolicyEngine")
    print("="*80)
    print(f"Total test cases: {total_tests}")
    print(f"Matches (within $1): {matches}")
    print(f"Match rate: {match_rate:.1f}%")
    print(f"")
    print(f"AGGREGATE COMPARISON:")
    print(f"Total expected tax: ${total_expected:,.0f}")
    print(f"Total PolicyEngine tax: ${total_pe:,.0f}")
    print(f"Aggregate difference: ${total_pe - total_expected:+,.0f} ({aggregate_diff_pct:+.1f}%)")
    print("")

    # Show failures
    failures = df[~df['matches']]
    if len(failures) > 0:
        print(f"FAILED TESTS ({len(failures)}):")
        print("-" * 80)
        for _, row in failures.iterrows():
            if pd.notna(row['policyengine_tax']):
                print(f"{row['test_name'][:50]:<50} Expected: ${row['expected_tax']:>8,.0f} PE: ${row['policyengine_tax']:>8,.0f} Diff: ${row['difference']:>+8,.0f}")
            else:
                print(f"{row['test_name'][:50]:<50} ERROR: {row.get('error', 'Unknown error')}")

    # Show largest discrepancies
    print(f"\nLARGEST ABSOLUTE DISCREPANCIES:")
    print("-" * 80)
    valid_results = df[df['policyengine_tax'].notna()]
    if len(valid_results) > 0:
        # Convert difference to numeric, handling any string values
        valid_results = valid_results.copy()
        valid_results['difference'] = pd.to_numeric(valid_results['difference'], errors='coerce')
        valid_results = valid_results[valid_results['difference'].notna()]

        if len(valid_results) > 0:
            largest_diff = valid_results.nlargest(min(5, len(valid_results)), 'difference')
            for _, row in largest_diff.iterrows():
                print(f"{row['test_name'][:50]:<50} ${row['difference']:>+8,.0f} ({row['percent_difference']:>+6.1f}%)")
        else:
            print("No valid numeric differences to display")
    else:
        print("No valid results to analyze")

    return {
        'total_tests': int(total_tests),
        'matches': int(matches),
        'match_rate': float(match_rate),
        'aggregate_diff_pct': float(aggregate_diff_pct),
        'total_expected': float(total_expected),
        'total_pe': float(total_pe)
    }

if __name__ == "__main__":
    print("Validating 26 USC 1 encoding against PolicyEngine...")

    # Run validation
    results_df = run_validation()

    # Generate report
    summary = generate_report(results_df)

    # Save detailed results
    results_df.to_csv('/Users/maxghenis/CosilicoAI/rac-us/statute/26/1/validation_results_pe.csv', index=False)
    print(f"\nDetailed results saved to validation_results_pe.csv")

    # Save summary
    with open('/Users/maxghenis/CosilicoAI/rac-us/statute/26/1/validation_summary_pe.json', 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"Summary saved to validation_summary_pe.json")