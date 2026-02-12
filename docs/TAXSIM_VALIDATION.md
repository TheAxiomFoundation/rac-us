# TAXSIM Validation Dashboard

*Last updated: 2025-12-26 09:49*

Comparison of PolicyEngine-US against NBER TAXSIM 35 API.

## Summary

- **Total test cases:** 90
- **Successful comparisons:** 90
- **Tax year:** 2023 (TAXSIM 35 max supported year)

## Accuracy Metrics

| Variable | N | Mean Diff | MAE | Max Abs Diff | Correlation | % Exact | % Within $10 | % Within $100 |
|----------|---|-----------|-----|--------------|-------------|---------|--------------|---------------|
| AGI | 90 | $-206,113 | $206,113 | $2,000,000 | nan | 3.3% | 3.3% | 3.3% |
| Taxable Income | 90 | $-185,445 | $185,445 | $1,972,300 | nan | 11.1% | 11.1% | 11.1% |
| Federal Tax | 90 | $-43,601 | $45,797 | $659,665 | nan | 4.4% | 4.4% | 5.6% |
| EITC | 90 | $-697 | $697 | $7,426 | nan | 80.0% | 80.0% | 80.0% |
| CTC | 90 | $-1,336 | $1,336 | $6,000 | nan | 62.2% | 62.2% | 62.2% |
| FICA | 90 | $-20,718 | $20,718 | $111,843 | nan | 3.3% | 3.3% | 3.3% |
| AMTI | 87 | $-211,036 | $211,036 | $2,000,000 | nan | 0.0% | 0.0% | 0.0% |

## Detailed Comparison

### Sample Scenarios

| Scenario | PE Tax | TS Tax | Diff | PE EITC | TS EITC | PE CTC | TS CTC |
|----------|--------|--------|------|---------|---------|--------|--------|
| Single $15,000 | $0 | $-88 | $88 | $0 | $202 | $0 | $0 |
| Single $25,000 | $0 | $1,118 | $-1,118 | $0 | $0 | $0 | $0 |
| Single $40,000 | $0 | $2,918 | $-2,918 | $0 | $0 | $0 | $0 |
| Single $60,000 | $0 | $5,460 | $-5,460 | $0 | $0 | $0 | $0 |
| Single $80,000 | $0 | $9,860 | $-9,860 | $0 | $0 | $0 | $0 |
| Single $120,000 | $0 | $18,876 | $-18,876 | $0 | $0 | $0 | $0 |
| Single $200,000 | $0 | $38,400 | $-38,400 | $0 | $0 | $0 | $0 |
| Single $400,000 | $0 | $107,047 | $-107,047 | $0 | $0 | $0 | $0 |
| MFJ $40,000 | $0 | $1,230 | $-1,230 | $0 | $0 | $0 | $0 |
| MFJ $80,000 | $0 | $5,836 | $-5,836 | $0 | $0 | $0 | $0 |
| MFJ $120,000 | $0 | $10,921 | $-10,921 | $0 | $0 | $0 | $0 |
| MFJ $200,000 | $0 | $28,521 | $-28,521 | $0 | $0 | $0 | $0 |
| MFJ $400,000 | $0 | $76,800 | $-76,800 | $0 | $0 | $0 | $0 |
| HoH $15,000 + 1 kids | $0 | $-5,597 | $5,597 | $0 | $3,997 | $0 | $1,600 |
| HoH $15,000 + 2 kids | $0 | $-7,875 | $7,875 | $0 | $6,000 | $0 | $1,875 |
| HoH $15,000 + 3 kids | $0 | $-8,625 | $8,625 | $0 | $6,750 | $0 | $1,875 |
| HoH $20,000 + 1 kids | $0 | $-5,597 | $5,597 | $0 | $3,997 | $0 | $1,600 |
| HoH $20,000 + 2 kids | $0 | $-9,225 | $9,225 | $0 | $6,600 | $0 | $2,625 |
| HoH $20,000 + 3 kids | $0 | $-10,051 | $10,051 | $0 | $7,426 | $0 | $2,625 |
| HoH $30,000 + 1 kids | $0 | $-3,728 | $3,728 | $0 | $2,648 | $0 | $2,000 |
| HoH $30,000 + 2 kids | $0 | $-7,902 | $7,902 | $0 | $4,822 | $0 | $4,000 |
| HoH $30,000 + 3 kids | $0 | $-9,772 | $9,772 | $0 | $5,648 | $0 | $5,045 |
| HoH $40,000 + 1 kids | $0 | $-1,060 | $1,060 | $0 | $1,050 | $0 | $2,000 |
| HoH $40,000 + 2 kids | $0 | $-4,726 | $4,726 | $0 | $2,716 | $0 | $4,000 |
| HoH $40,000 + 3 kids | $0 | $-7,552 | $7,552 | $0 | $3,542 | $0 | $6,000 |
| HoH $50,000 + 1 kids | $0 | $1,190 | $-1,190 | $0 | $0 | $0 | $2,000 |
| HoH $50,000 + 2 kids | $0 | $-1,420 | $1,420 | $0 | $610 | $0 | $4,000 |
| HoH $50,000 + 3 kids | $0 | $-4,246 | $4,246 | $0 | $1,436 | $0 | $6,000 |
| MFJ $50,000 + 1 kids | $0 | $-265 | $265 | $0 | $501 | $0 | $2,000 |
| MFJ $50,000 + 2 kids | $0 | $-3,756 | $3,756 | $0 | $1,992 | $0 | $4,000 |

### Largest Discrepancies (Federal Tax)

| Scenario | PE Tax | TS Tax | Diff | PE AGI | TS AGI |
|----------|--------|--------|------|--------|--------|
| AMT phaseout - Joint $2,000,000 | $0 | $659,665 | $-659,665 | $0 | $2,000,000 |
| AMT phaseout - Joint $1,500,000 | $0 | $474,665 | $-474,665 | $0 | $1,500,000 |
| AMT phaseout - Joint $1,200,000 | $0 | $363,665 | $-363,665 | $0 | $1,200,000 |
| AMT - High income $1,000,000 | $0 | $285,114 | $-285,114 | $0 | $1,000,000 |
| AMT - Single high $800,000 | $0 | $245,232 | $-245,232 | $0 | $800,000 |
| AMT - High income $750,000 | $0 | $192,614 | $-192,614 | $0 | $750,000 |
| AMT - Single high $600,000 | $0 | $171,394 | $-171,394 | $0 | $600,000 |
| MFJ $500,000 + 1 kids | $0 | $109,094 | $-109,094 | $0 | $500,000 |
| MFJ $500,000 + 2 kids | $0 | $109,094 | $-109,094 | $0 | $500,000 |
| MFJ $500,000 + 3 kids | $0 | $108,094 | $-108,094 | $0 | $500,000 |

### EITC Discrepancies

| Scenario | PE EITC | TS EITC | Diff | Wages | # Kids |
|----------|---------|---------|------|-------|--------|
| HoH $20,000 + 3 kids | $0 | $7,426 | $-7,426 | $20,000 | 3 |
| HoH $15,000 + 3 kids | $0 | $6,750 | $-6,750 | $15,000 | 3 |
| HoH $20,000 + 2 kids | $0 | $6,600 | $-6,600 | $20,000 | 2 |
| HoH $15,000 + 2 kids | $0 | $6,000 | $-6,000 | $15,000 | 2 |
| HoH $30,000 + 3 kids | $0 | $5,648 | $-5,648 | $30,000 | 3 |
| HoH $30,000 + 2 kids | $0 | $4,822 | $-4,822 | $30,000 | 2 |
| HoH $15,000 + 1 kids | $0 | $3,997 | $-3,997 | $15,000 | 1 |
| HoH $20,000 + 1 kids | $0 | $3,997 | $-3,997 | $20,000 | 1 |
| HoH $40,000 + 3 kids | $0 | $3,542 | $-3,542 | $40,000 | 3 |
| MFJ $50,000 + 3 kids | $0 | $2,818 | $-2,818 | $30,000 | 3 |
| HoH $40,000 + 2 kids | $0 | $2,716 | $-2,716 | $40,000 | 2 |
| HoH $30,000 + 1 kids | $0 | $2,648 | $-2,648 | $30,000 | 1 |
| MFJ $50,000 + 2 kids | $0 | $1,992 | $-1,992 | $30,000 | 2 |
| HoH $50,000 + 3 kids | $0 | $1,436 | $-1,436 | $50,000 | 3 |
| HoH $40,000 + 1 kids | $0 | $1,050 | $-1,050 | $40,000 | 1 |

### CTC Discrepancies

| Scenario | PE CTC | TS CTC | TS Refund | Diff | # Kids |
|----------|--------|--------|-----------|------|--------|
| HoH $40,000 + 3 kids | $0 | $1,990 | $4,010 | $-6,000 | 3 |
| HoH $50,000 + 3 kids | $0 | $3,190 | $2,810 | $-6,000 | 3 |
| MFJ $50,000 + 3 kids | $0 | $2,236 | $3,764 | $-6,000 | 3 |
| MFJ $75,000 + 3 kids | $0 | $5,236 | $764 | $-6,000 | 3 |
| MFJ $100,000 + 3 kids | $0 | $6,000 | $0 | $-6,000 | 3 |
| MFJ $150,000 + 3 kids | $0 | $6,000 | $0 | $-6,000 | 3 |
| MFJ $200,000 + 3 kids | $0 | $6,000 | $0 | $-6,000 | 3 |
| MFJ $400,000 + 3 kids | $0 | $6,000 | $0 | $-6,000 | 3 |
| HoH $30,000 + 3 kids | $0 | $920 | $4,125 | $-5,045 | 3 |
| HoH $30,000 + 2 kids | $0 | $920 | $3,080 | $-4,000 | 2 |
| HoH $40,000 + 2 kids | $0 | $1,990 | $2,010 | $-4,000 | 2 |
| HoH $50,000 + 2 kids | $0 | $3,190 | $810 | $-4,000 | 2 |
| MFJ $50,000 + 2 kids | $0 | $2,236 | $1,764 | $-4,000 | 2 |
| MFJ $75,000 + 2 kids | $0 | $4,000 | $0 | $-4,000 | 2 |
| MFJ $100,000 + 2 kids | $0 | $4,000 | $0 | $-4,000 | 2 |

## Test Scenario Categories

1. **Single filers** - Income levels $15K to $400K
2. **Married filing jointly** - Income levels $40K to $400K
3. **Head of Household with children** - EITC eligibility scenarios
4. **MFJ with children** - CTC eligibility scenarios
5. **Self-employment income** - SE tax calculations
6. **Mixed wages + self-employment** - Combined income
7. **Investment income** - Dividends and interest
8. **Capital gains** - Long-term capital gains
9. **High income itemized** - Mortgage and property tax deductions
10. **Social Security recipients** - Benefit taxation

## Known Differences

### TAXSIM vs PolicyEngine

- **Dependent handling**: TAXSIM uses `depx` count and `age1-age3` for ages; PolicyEngine models individual dependents with specific attributes
- **Head of Household**: Filing status determination may differ
- **EITC phase-out**: Minor differences in earned income calculation
- **CTC refundability**: ACTC (refundable portion) calculation differs
- **Self-employment tax**: TAXSIM may use different SE income calculation

## Methodology

1. Generate standardized test cases covering key scenarios
2. Submit batch to TAXSIM 35 API (https://taxsim.nber.org/taxsim35/)
3. Run equivalent calculations in PolicyEngine-US
4. Compare key outputs: AGI, taxable income, tax liability, credits
5. Track discrepancies and investigate systematic differences

## References

- [TAXSIM 35 Documentation](https://taxsim.nber.org/taxsim35/)
- [PolicyEngine-US Documentation](https://policyengine.org/us/research)
- [RAC US Encodings](https://github.com/RulesFoundation/rac-us)