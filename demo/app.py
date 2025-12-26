#!/usr/bin/env python3
"""
Cosilico Demo App

Shows the full pipeline from source document to calculation:
1. Lawarchive: Fetched source document (USC XML)
2. Encoding: .rac formula that references the source
3. Parameters: Resolved values from statute + guidance
4. Calculation: Run on sample data

Usage:
    streamlit run demo/app.py
    # or
    python demo/app.py  # CLI mode
"""

import json
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try to import streamlit, fall back to CLI
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False


@dataclass
class SourceDocument:
    """A source document from lawarchive."""
    citation: str
    path: str
    effective_date: str
    accessed_date: str
    content_preview: str
    source_url: str


@dataclass
class Encoding:
    """A .rac encoding."""
    variable: str
    citation: str
    formula_preview: str
    source_path: str


@dataclass
class Parameters:
    """Resolved parameters for a tax year."""
    tax_year: int
    values: dict
    sources: list


@dataclass
class Calculation:
    """A calculation result."""
    variable: str
    inputs: dict
    result: float
    breakdown: dict


# Sample data - in production this would come from actual files
SAMPLE_SOURCE = SourceDocument(
    citation="26 USC § 32",
    path="us/statute/26/32/2025-01-01",
    effective_date="2025-01-01",
    accessed_date="2025-12-12",
    content_preview="""§ 32. Earned income

(a) Allowance of credit
(1) In general
In the case of an eligible individual, there shall be allowed as a
credit against the tax imposed by this subtitle for the taxable year
an amount equal to the credit percentage of so much of the taxpayer's
earned income for the taxable year as does not exceed the earned
income amount.

(2) Limitation
The amount of the credit allowable to a taxpayer under paragraph (1)
for any taxable year shall not exceed the excess (if any) of—
(A) the credit percentage of the earned income amount, over
(B) the phaseout percentage of so much of the adjusted gross income
    (or, if greater, the earned income) of the taxpayer for the
    taxable year as exceeds the phaseout amount.""",
    source_url="https://uscode.house.gov/download/releasepoints/us/pl/119/46/xml_usc26@119-46.zip"
)

SAMPLE_ENCODING = Encoding(
    variable="eitc",
    citation="26 USC § 32",
    source_path="us/statute/26/32/2025-01-01",
    formula_preview="""# 26 USC § 32 - Earned Income Tax Credit
# Source: lawarchive://us/statute/26/32/2025-01-01

source {
    lawarchive: us/statute/26/32/2025-01-01
    citation: "26 USC § 32"
}

variable eitc {
    entity TaxUnit
    period Year
    dtype Money

    formula {
        # § 32(a)(1): Credit = credit_pct * min(earned_income, earned_income_amount)
        let credit_base = credit_percentage * min(earned_income, earned_income_amount)

        # § 32(a)(2): Limitation - phaseout above phaseout_amount
        let excess_income = max(0, max(agi, earned_income) - phaseout_amount)
        let phaseout = phaseout_percentage * excess_income

        return max(0, credit_base - phaseout)
    }
}"""
)

SAMPLE_PARAMS = Parameters(
    tax_year=2025,
    values={
        "credit_percentage": {0: 0.0765, 1: 0.34, 2: 0.40, 3: 0.45},
        "phaseout_percentage": {0: 0.0765, 1: 0.1598, 2: 0.2106, 3: 0.2106},
        "earned_income_amount": {0: 8260, 1: 12730, 2: 17880, 3: 17880},
        "phaseout_amount_single": {0: 10620, 1: 23350, 2: 23350, 3: 23350},
        "phaseout_amount_joint": {0: 17730, 1: 30470, 2: 30470, 3: 30470},
        "max_credit": {0: 649, 1: 4328, 2: 7152, 3: 8046},
        "investment_income_limit": 11950,
    },
    sources=[
        "Statute: 26 USC § 32(b)(1) - percentages",
        "Guidance: Rev. Proc. 2024-40 - TY 2025 amounts",
    ]
)


def calculate_eitc(
    earned_income: float,
    agi: float,
    num_children: int,
    filing_status: str,
    params: Parameters,
) -> Calculation:
    """Calculate EITC using the formula from § 32."""
    n = min(num_children, 3)  # Cap at 3+ children

    # Get parameters for this number of children
    credit_pct = params.values["credit_percentage"][n]
    phaseout_pct = params.values["phaseout_percentage"][n]
    earned_amount = params.values["earned_income_amount"][n]

    if filing_status == "joint":
        phaseout_start = params.values["phaseout_amount_joint"][n]
    else:
        phaseout_start = params.values["phaseout_amount_single"][n]

    # § 32(a)(1): Credit base
    credit_base = credit_pct * min(earned_income, earned_amount)

    # § 32(a)(2): Phaseout
    income_for_phaseout = max(agi, earned_income)
    excess_income = max(0, income_for_phaseout - phaseout_start)
    phaseout = phaseout_pct * excess_income

    # Final credit
    credit = max(0, credit_base - phaseout)

    return Calculation(
        variable="eitc",
        inputs={
            "earned_income": earned_income,
            "agi": agi,
            "num_children": num_children,
            "filing_status": filing_status,
            "tax_year": params.tax_year,
        },
        result=round(credit),
        breakdown={
            "credit_percentage": credit_pct,
            "earned_income_amount": earned_amount,
            "credit_base": round(credit_base, 2),
            "phaseout_start": phaseout_start,
            "excess_income": excess_income,
            "phaseout_amount": round(phaseout, 2),
            "final_credit": round(credit),
        }
    )


def run_streamlit():
    """Run the Streamlit web app."""
    st.set_page_config(page_title="Cosilico Demo", layout="wide")
    st.title("Cosilico: Executable Tax Law")

    st.markdown("""
    This demo shows how Cosilico connects source documents to calculations:

    **Lawarchive** → **Encoding** → **Parameters** → **Calculation**
    """)

    # Tabs for each layer
    tab1, tab2, tab3, tab4 = st.tabs([
        "1. Source Document",
        "2. Encoding (.rac)",
        "3. Parameters",
        "4. Calculate"
    ])

    with tab1:
        st.header("Source Document from Lawarchive")
        st.markdown(f"**Citation:** {SAMPLE_SOURCE.citation}")
        st.markdown(f"**Path:** `lawarchive://{SAMPLE_SOURCE.path}`")
        st.markdown(f"**Effective Date:** {SAMPLE_SOURCE.effective_date}")
        st.markdown(f"**Accessed:** {SAMPLE_SOURCE.accessed_date}")
        st.markdown(f"**Source URL:** [{SAMPLE_SOURCE.source_url}]({SAMPLE_SOURCE.source_url})")

        st.subheader("Content Preview")
        st.code(SAMPLE_SOURCE.content_preview, language="text")

    with tab2:
        st.header("Encoding: .rac File")
        st.markdown(f"**Variable:** `{SAMPLE_ENCODING.variable}`")
        st.markdown(f"**Source:** `lawarchive://{SAMPLE_ENCODING.source_path}`")

        st.subheader("Formula")
        st.code(SAMPLE_ENCODING.formula_preview, language="python")

        st.info("""
        The encoding:
        - References the source document via `lawarchive://` path
        - Translates statute language into executable formulas
        - Uses symbolic parameter names that resolve from guidance
        """)

    with tab3:
        st.header(f"Parameters: Tax Year {SAMPLE_PARAMS.tax_year}")

        st.subheader("Sources")
        for src in SAMPLE_PARAMS.sources:
            st.markdown(f"- {src}")

        st.subheader("Resolved Values")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Credit Percentages** (§ 32(b)(1))")
            for n, pct in SAMPLE_PARAMS.values["credit_percentage"].items():
                label = f"{n} children" if n > 0 else "No children"
                st.markdown(f"- {label}: {pct*100:.2f}%")

        with col2:
            st.markdown("**Maximum Credits** (§ 32(b)(2))")
            for n, amt in SAMPLE_PARAMS.values["max_credit"].items():
                label = f"{n} children" if n > 0 else "No children"
                st.markdown(f"- {label}: ${amt:,}")

    with tab4:
        st.header("Calculate EITC")

        col1, col2 = st.columns(2)

        with col1:
            earned_income = st.number_input("Earned Income", value=25000, step=1000)
            agi = st.number_input("AGI", value=25000, step=1000)

        with col2:
            num_children = st.selectbox("Number of Qualifying Children", [0, 1, 2, 3])
            filing_status = st.selectbox("Filing Status", ["single", "joint"])

        if st.button("Calculate"):
            result = calculate_eitc(
                earned_income=earned_income,
                agi=agi,
                num_children=num_children,
                filing_status=filing_status,
                params=SAMPLE_PARAMS,
            )

            st.success(f"**EITC: ${result.result:,}**")

            st.subheader("Calculation Breakdown")
            st.json(result.breakdown)

            st.subheader("Citation Chain")
            st.markdown(f"""
            1. **Source:** `lawarchive://us/statute/26/32/2025-01-01`
            2. **Encoding:** `cosilico-us://26/32/eitc.rac`
            3. **Parameters:** Rev. Proc. 2024-40 (TY {SAMPLE_PARAMS.tax_year})
            4. **Result:** ${result.result:,}
            """)


def run_cli():
    """Run CLI demo."""
    print("=" * 60)
    print("COSILICO DEMO: Executable Tax Law")
    print("=" * 60)

    print("\n1. SOURCE DOCUMENT (lawarchive)")
    print("-" * 40)
    print(f"Citation: {SAMPLE_SOURCE.citation}")
    print(f"Path: lawarchive://{SAMPLE_SOURCE.path}")
    print(f"Effective: {SAMPLE_SOURCE.effective_date}")
    print(f"\nPreview:\n{SAMPLE_SOURCE.content_preview[:500]}...")

    print("\n2. ENCODING (.rac)")
    print("-" * 40)
    print(f"Variable: {SAMPLE_ENCODING.variable}")
    print(f"Source: lawarchive://{SAMPLE_ENCODING.source_path}")
    print(f"\nFormula Preview:\n{SAMPLE_ENCODING.formula_preview[:600]}...")

    print("\n3. PARAMETERS (TY 2025)")
    print("-" * 40)
    print("Sources:")
    for src in SAMPLE_PARAMS.sources:
        print(f"  - {src}")
    print("\nMax Credits:")
    for n, amt in SAMPLE_PARAMS.values["max_credit"].items():
        label = f"{n} children" if n > 0 else "No children"
        print(f"  {label}: ${amt:,}")

    print("\n4. CALCULATION")
    print("-" * 40)

    # Sample calculation
    result = calculate_eitc(
        earned_income=25000,
        agi=25000,
        num_children=2,
        filing_status="single",
        params=SAMPLE_PARAMS,
    )

    print(f"Inputs: {result.inputs}")
    print(f"\nBreakdown:")
    for k, v in result.breakdown.items():
        print(f"  {k}: {v}")
    print(f"\n>>> EITC: ${result.result:,}")

    print("\n" + "=" * 60)
    print("Citation Chain:")
    print(f"  1. lawarchive://us/statute/26/32/2025-01-01")
    print(f"  2. cosilico-us://26/32/eitc.rac")
    print(f"  3. Rev. Proc. 2024-40 (TY 2025)")
    print(f"  4. Result: ${result.result:,}")


if __name__ == "__main__":
    if HAS_STREAMLIT and len(sys.argv) == 1:
        # If run without args and streamlit available, suggest streamlit
        print("Run with: streamlit run demo/app.py")
        print("\nOr run CLI demo:")
        run_cli()
    else:
        run_cli()
