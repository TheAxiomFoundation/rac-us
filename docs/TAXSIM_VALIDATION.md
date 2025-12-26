# TAXSIM Validation Dashboard

*Last updated: 2025-12-26 09:13*

Comparison of PolicyEngine-US against NBER TAXSIM 35 API.

## Summary

- **Total test cases:** 81
- **Successful comparisons:** 81
- **Tax year:** 2023 (TAXSIM 35 max supported year)

## Accuracy Metrics

| Variable | N | Mean Diff | MAE | Max Abs Diff | Correlation | % Exact | % Within $10 | % Within $100 |
|----------|---|-----------|-----|--------------|-------------|---------|--------------|---------------|
| AGI | 81 | $-5 | $5 | $409 | 1.000 | 98.8% | 98.8% | 98.8% |
| Taxable Income | 81 | $-1,348 | $1,461 | $35,117 | 0.999 | 80.2% | 80.2% | 80.2% |
| Federal Tax | 81 | $-137 | $479 | $8,428 | 0.999 | 54.3% | 72.8% | 79.0% |
| EITC | 81 | $0 | $1 | $5 | 1.000 | 81.5% | 100.0% | 100.0% |
| CTC | 81 | $157 | $157 | $4,125 | 0.957 | 91.4% | 91.4% | 91.4% |
| FICA | 81 | $-10,499 | $10,499 | $44,910 | 0.659 | 7.4% | 7.4% | 7.4% |

## Detailed Comparison

### Sample Scenarios

| Scenario | PE Tax | TS Tax | Diff | PE EITC | TS EITC | PE CTC | TS CTC |
|----------|--------|--------|------|---------|---------|--------|--------|
| Single $15,000 | $-87 | $-88 | $0 | $202 | $202 | $0 | $0 |
| Single $25,000 | $1,118 | $1,118 | $0 | $0 | $0 | $0 | $0 |
| Single $40,000 | $2,918 | $2,918 | $0 | $0 | $0 | $0 | $0 |
| Single $60,000 | $5,460 | $5,460 | $0 | $0 | $0 | $0 | $0 |
| Single $80,000 | $9,860 | $9,860 | $0 | $0 | $0 | $0 | $0 |
| Single $120,000 | $18,876 | $18,876 | $0 | $0 | $0 | $0 | $0 |
| Single $200,000 | $38,400 | $38,400 | $0 | $0 | $0 | $0 | $0 |
| Single $400,000 | $107,047 | $107,047 | $0 | $0 | $0 | $0 | $0 |
| MFJ $40,000 | $1,230 | $1,230 | $0 | $0 | $0 | $0 | $0 |
| MFJ $80,000 | $5,836 | $5,836 | $0 | $0 | $0 | $0 | $0 |
| MFJ $120,000 | $10,921 | $10,921 | $0 | $0 | $0 | $0 | $0 |
| MFJ $200,000 | $28,521 | $28,521 | $0 | $0 | $0 | $0 | $0 |
| MFJ $400,000 | $76,800 | $76,800 | $0 | $0 | $0 | $0 | $0 |
| HoH $15,000 + 1 kids | $-5,595 | $-5,597 | $2 | $3,995 | $3,997 | $2,000 | $1,600 |
| HoH $15,000 + 2 kids | $-7,875 | $-7,875 | $0 | $6,000 | $6,000 | $4,000 | $1,875 |
| HoH $15,000 + 3 kids | $-8,625 | $-8,625 | $0 | $6,750 | $6,750 | $6,000 | $1,875 |
| HoH $20,000 + 1 kids | $-5,595 | $-5,597 | $2 | $3,995 | $3,997 | $2,000 | $1,600 |
| HoH $20,000 + 2 kids | $-9,229 | $-9,225 | $-4 | $6,604 | $6,600 | $4,000 | $2,625 |
| HoH $20,000 + 3 kids | $-10,055 | $-10,051 | $-4 | $7,430 | $7,426 | $6,000 | $2,625 |
| HoH $30,000 + 1 kids | $-3,726 | $-3,728 | $2 | $2,646 | $2,648 | $2,000 | $2,000 |
| HoH $30,000 + 2 kids | $-7,907 | $-7,902 | $-5 | $4,827 | $4,822 | $4,000 | $4,000 |
| HoH $30,000 + 3 kids | $-9,778 | $-9,772 | $-5 | $5,653 | $5,648 | $6,000 | $5,045 |
| HoH $40,000 + 1 kids | $-1,058 | $-1,060 | $2 | $1,048 | $1,050 | $2,000 | $2,000 |
| HoH $40,000 + 2 kids | $-4,731 | $-4,726 | $-5 | $2,721 | $2,716 | $4,000 | $4,000 |
| HoH $40,000 + 3 kids | $-7,557 | $-7,552 | $-5 | $3,547 | $3,542 | $6,000 | $6,000 |
| HoH $50,000 + 1 kids | $1,190 | $1,190 | $0 | $0 | $0 | $2,000 | $2,000 |
| HoH $50,000 + 2 kids | $-1,425 | $-1,420 | $-5 | $615 | $610 | $4,000 | $4,000 |
| HoH $50,000 + 3 kids | $-4,251 | $-4,246 | $-5 | $1,441 | $1,436 | $6,000 | $6,000 |
| MFJ $50,000 + 1 kids | $-263 | $-265 | $2 | $499 | $501 | $2,000 | $2,000 |
| MFJ $50,000 + 2 kids | $-3,760 | $-3,756 | $-4 | $1,996 | $1,992 | $4,000 | $4,000 |

### Largest Discrepancies (Federal Tax)

| Scenario | PE Tax | TS Tax | Diff | PE AGI | TS AGI |
|----------|--------|--------|------|--------|--------|
| Self-employed $200,000 | $26,720 | $35,148 | $-8,428 | $187,389 | $187,799 |
| Self-employed $150,000 | $17,506 | $23,533 | $-6,027 | $139,403 | $139,403 |
| Wages $100,000 + Div $50,000 | $26,076 | $21,760 | $4,316 | $150,000 | $150,000 |
| Wages $50,000 + Div $50,000 | $14,260 | $10,347 | $3,914 | $100,000 | $100,000 |
| Self-employed $100,000 | $9,226 | $12,706 | $-3,480 | $92,935 | $92,935 |
| Wages $80,000 + SE $50,000 | $18,198 | $20,428 | $-2,230 | $126,468 | $126,468 |
| Wages $40,000 + SE $50,000 | $9,239 | $11,283 | $-2,045 | $86,468 | $86,468 |
| Wages $50,000 + Div $20,000 | $7,660 | $5,847 | $1,814 | $70,000 | $70,000 |
| Wages $100,000 + Div $20,000 | $18,876 | $17,260 | $1,616 | $120,000 | $120,000 |
| Self-employed $60,000 | $3,803 | $4,809 | $-1,006 | $55,761 | $55,761 |

### EITC Discrepancies

| Scenario | PE EITC | TS EITC | Diff | Wages | # Kids |
|----------|---------|---------|------|-------|--------|
| HoH $30,000 + 3 kids | $5,653 | $5,648 | $5 | $30,000 | 3 |
| HoH $50,000 + 3 kids | $1,441 | $1,436 | $5 | $50,000 | 3 |
| HoH $40,000 + 3 kids | $3,547 | $3,542 | $5 | $40,000 | 3 |
| HoH $30,000 + 2 kids | $4,827 | $4,822 | $5 | $30,000 | 2 |
| HoH $50,000 + 2 kids | $615 | $610 | $5 | $50,000 | 2 |
| HoH $40,000 + 2 kids | $2,721 | $2,716 | $5 | $40,000 | 2 |
| MFJ $50,000 + 3 kids | $2,822 | $2,818 | $4 | $30,000 | 3 |
| HoH $20,000 + 3 kids | $7,430 | $7,426 | $4 | $20,000 | 3 |
| MFJ $50,000 + 2 kids | $1,996 | $1,992 | $4 | $30,000 | 2 |
| HoH $20,000 + 2 kids | $6,604 | $6,600 | $4 | $20,000 | 2 |
| HoH $15,000 + 1 kids | $3,995 | $3,997 | $-2 | $15,000 | 1 |
| HoH $20,000 + 1 kids | $3,995 | $3,997 | $-2 | $20,000 | 1 |
| MFJ $50,000 + 1 kids | $499 | $501 | $-2 | $30,000 | 1 |
| HoH $30,000 + 1 kids | $2,646 | $2,648 | $-2 | $30,000 | 1 |
| HoH $40,000 + 1 kids | $1,048 | $1,050 | $-2 | $40,000 | 1 |

### CTC Discrepancies

| Scenario | PE CTC | TS CTC | TS Refund | Diff | # Kids |
|----------|--------|--------|-----------|------|--------|
| HoH $15,000 + 3 kids | $6,000 | $0 | $1,875 | $4,125 | 3 |
| HoH $20,000 + 3 kids | $6,000 | $0 | $2,625 | $3,375 | 3 |
| HoH $15,000 + 2 kids | $4,000 | $0 | $1,875 | $2,125 | 2 |
| HoH $20,000 + 2 kids | $4,000 | $0 | $2,625 | $1,375 | 2 |
| HoH $30,000 + 3 kids | $6,000 | $920 | $4,125 | $955 | 3 |
| HoH $15,000 + 1 kids | $2,000 | $0 | $1,600 | $400 | 1 |
| HoH $20,000 + 1 kids | $2,000 | $0 | $1,600 | $400 | 1 |
| HoH $30,000 + 1 kids | $2,000 | $920 | $1,080 | $0 | 1 |
| HoH $30,000 + 2 kids | $4,000 | $920 | $3,080 | $0 | 2 |
| HoH $40,000 + 1 kids | $2,000 | $1,990 | $10 | $0 | 1 |
| HoH $40,000 + 2 kids | $4,000 | $1,990 | $2,010 | $0 | 2 |
| HoH $40,000 + 3 kids | $6,000 | $1,990 | $4,010 | $0 | 3 |
| HoH $50,000 + 1 kids | $2,000 | $2,000 | $0 | $0 | 1 |
| HoH $50,000 + 2 kids | $4,000 | $3,190 | $810 | $0 | 2 |
| HoH $50,000 + 3 kids | $6,000 | $3,190 | $2,810 | $0 | 3 |

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
- [Cosilico US Encodings](https://github.com/CosilicoAI/cosilico-us)