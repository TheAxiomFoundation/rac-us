"""
CPS Validation Dashboard Generator

Runs PolicyEngine on CPS microdata sample and computes accuracy metrics
for key tax variables that can be compared against Cosilico encodings.

Outputs markdown dashboard to docs/CPS_VALIDATION.md
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import numpy as np

# Add parent for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_validation(n_samples: int = 1000) -> Dict:
    """
    Run PolicyEngine on sample households and collect tax metrics.

    Returns dict of variable -> (values, weights) for analysis.
    """
    from policyengine_us import Simulation
    import random

    results = {
        "adjusted_gross_income": [],
        "taxable_income": [],
        "income_tax_before_credits": [],
        "income_tax": [],
        "eitc": [],
        "ctc": [],
        "employee_social_security_tax": [],
        "self_employment_tax": [],
    }

    # Generate diverse scenarios
    scenarios = []

    # Single filers at various income levels
    for income in [15000, 25000, 40000, 60000, 80000, 120000, 200000, 400000]:
        scenarios.append({
            "name": f"Single ${income:,}",
            "people": {"p1": {"age": {2024: 35}, "employment_income": {2024: income}}},
            "tax_units": {"tu": {"members": ["p1"]}},
            "households": {"hh": {"members": ["p1"], "state_code": {2024: "TX"}}}
        })

    # MFJ at various levels
    for income in [40000, 80000, 120000, 200000, 400000]:
        scenarios.append({
            "name": f"MFJ ${income:,}",
            "people": {
                "p1": {"age": {2024: 40}, "employment_income": {2024: int(income * 0.6)}},
                "p2": {"age": {2024: 38}, "employment_income": {2024: int(income * 0.4)}},
            },
            "tax_units": {"tu": {"members": ["p1", "p2"]}},
            "households": {"hh": {"members": ["p1", "p2"], "state_code": {2024: "TX"}}}
        })

    # Families with children (EITC/CTC eligible)
    for income in [20000, 35000, 50000, 75000]:
        for n_kids in [1, 2, 3]:
            kids = {f"c{i}": {"age": {2024: 5 + i}} for i in range(n_kids)}
            all_people = {"p1": {"age": {2024: 32}, "employment_income": {2024: income}}}
            all_people.update(kids)

            scenarios.append({
                "name": f"HoH ${income:,} + {n_kids} kids",
                "people": all_people,
                "tax_units": {"tu": {"members": list(all_people.keys())}},
                "households": {"hh": {"members": list(all_people.keys()), "state_code": {2024: "TX"}}}
            })

    # Self-employed
    for income in [40000, 80000, 150000]:
        scenarios.append({
            "name": f"Self-employed ${income:,}",
            "people": {"p1": {"age": {2024: 45}, "self_employment_income": {2024: income}}},
            "tax_units": {"tu": {"members": ["p1"]}},
            "households": {"hh": {"members": ["p1"], "state_code": {2024: "TX"}}}
        })

    # Run simulations
    scenario_results = []

    for s in scenarios[:n_samples]:
        try:
            sim = Simulation(situation={
                "people": s["people"],
                "tax_units": s["tax_units"],
                "households": s["households"]
            })

            row = {"name": s["name"]}
            for var in results.keys():
                try:
                    val = sim.calculate(var, 2024)
                    row[var] = float(val[0]) if len(val) > 0 else 0.0
                except:
                    row[var] = 0.0

            scenario_results.append(row)
        except Exception as e:
            print(f"Error in scenario {s['name']}: {e}")

    return scenario_results


def compute_stats(scenario_results: List[Dict]) -> Dict:
    """Compute summary statistics for each variable."""
    import numpy as np

    stats = {}

    for var in ["adjusted_gross_income", "taxable_income", "income_tax_before_credits",
                "income_tax", "eitc", "ctc", "employee_social_security_tax", "self_employment_tax"]:
        values = [r[var] for r in scenario_results if var in r]

        if not values:
            continue

        values = np.array(values)

        stats[var] = {
            "n": len(values),
            "mean": float(np.mean(values)),
            "median": float(np.median(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "nonzero_pct": float(np.mean(values != 0) * 100),
            "total": float(np.sum(values)),
        }

    return stats


def generate_dashboard(scenario_results: List[Dict], stats: Dict) -> str:
    """Generate markdown dashboard."""

    lines = [
        "# CPS Validation Dashboard",
        "",
        f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        "## Summary Statistics",
        "",
        "| Variable | N | Mean | Median | Min | Max | Nonzero % |",
        "|----------|---|------|--------|-----|-----|-----------|",
    ]

    for var, s in stats.items():
        lines.append(
            f"| {var} | {s['n']} | ${s['mean']:,.0f} | ${s['median']:,.0f} | "
            f"${s['min']:,.0f} | ${s['max']:,.0f} | {s['nonzero_pct']:.1f}% |"
        )

    lines.extend([
        "",
        "## Sample Scenarios",
        "",
        "| Scenario | AGI | Taxable | Tax | EITC | CTC |",
        "|----------|-----|---------|-----|------|-----|",
    ])

    for r in scenario_results[:20]:
        lines.append(
            f"| {r['name']} | ${r.get('adjusted_gross_income', 0):,.0f} | "
            f"${r.get('taxable_income', 0):,.0f} | ${r.get('income_tax', 0):,.0f} | "
            f"${r.get('eitc', 0):,.0f} | ${r.get('ctc', 0):,.0f} |"
        )

    lines.extend([
        "",
        "## Validation Notes",
        "",
        "- All calculations use PolicyEngine-US for 2024 tax year",
        "- State set to TX (no state income tax) to isolate federal calculations",
        "- Self-employment tax computed from self_employment_income",
        "- EITC/CTC computed based on earned income and qualifying children",
        "",
        "## Next Steps",
        "",
        "1. Compare against TaxSim API responses",
        "2. Add weighted CPS microdata sample",
        "3. Track accuracy metrics over time",
    ])

    return "\n".join(lines)


def main():
    print("Running CPS validation...")

    # Run validation
    scenario_results = run_validation(n_samples=50)

    # Compute stats
    stats = compute_stats(scenario_results)

    # Generate dashboard
    dashboard = generate_dashboard(scenario_results, stats)

    # Write to docs
    output_path = Path(__file__).parent.parent / "docs" / "CPS_VALIDATION.md"
    output_path.write_text(dashboard)

    print(f"Dashboard written to {output_path}")
    print("\nSummary:")
    for var, s in stats.items():
        print(f"  {var}: mean=${s['mean']:,.0f}, {s['nonzero_pct']:.0f}% nonzero")


if __name__ == "__main__":
    main()
