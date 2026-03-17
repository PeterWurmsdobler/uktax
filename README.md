# UK Tax Calculator: Fixing the 60% Marginal Rate Trap

Analysis tool for the UK income tax system, with a focus on the **60% marginal rate trap** that affects earners between £100,000-£125,140.

## The Problem

The UK tax system has a quirk where the personal allowance (£12,570) is withdrawn at £1 per £2 earned above £100,000. This creates:

- **60%+ marginal rate** between £100k-£125k (40% income tax + 20% from PA loss + 2% NI)
- **Higher tax burden than those earning £200k+** (who pay only 47%)
- **Perverse incentives** to avoid earning in this range

**Example**: Earning an extra £10,000 at £110,000 nets only £3,800 after tax.

## Installation

```bash
git clone https://github.com/PeterWurmsdobler/uktax.git
cd uktax
pip install -e .
```

## CLI Usage

The `uktax` command provides four subcommands:

### 1. Calculate Tax Revenue
```bash
uktax revenue [--population 100000] [--bin-size 1000]
```
Calculates total tax revenue from UK income distribution.

### 2. Visualize Income Distribution
```bash
uktax plot-income [--population 100000]
```
Creates plots showing income distribution with percentile markers.

### 3. Visualize Tax Rates
```bash
uktax plot-tax [--max-income-range 160000]
```
Shows marginal and effective tax rates, highlighting the 60% trap region.

### 4. Analyze Tax Reform
```bash
# Find revenue-neutral reform rate
uktax plot-reform --scenario revenue-neutral

# Test specific additional rate
uktax plot-reform --scenario fixed-rate --fixed-rate-percent 45
```

Compares current system vs reformed system (no PA taper, higher rate threshold at £100k).

**Key Finding**: Revenue-neutral reform requires **46.9% additional rate** (up from 45%), eliminates the trap, and affects only 4% of taxpayers.

## Python API

### Basic Tax Calculation

```python
from uktax import UKTaxCalculator2023

calc = UKTaxCalculator2023()

# Calculate for £110,000 income (in the trap)
income = 110000
total_tax, income_tax, ni = calc.calculate_total_deductions(income)
marginal_rate = calc.calculate_marginal_rate(income)

print(f"Total tax: £{total_tax:,.0f}")
print(f"Marginal rate: {marginal_rate:.1f}%")  # ~52%
```

### Compare Current vs Reformed

```python
from uktax import (
    UKTaxCalculator2023,
    UKTaxCalculatorReformed,
    IncomeDistributionData,
    IncomeHistogram,
    UK_INCOME_2023,
    optimize_additional_rate_for_revenue
)

# Create income distribution
distribution = IncomeDistributionData.from_list(UK_INCOME_2023, start_percentile=1)
histogram = IncomeHistogram.from_distribution(distribution, population_size=100000, bin_size=1000)

# Calculate baseline revenue
current = UKTaxCalculator2023()
baseline_revenue = sum(
    current.calculate_total_deductions(income)[0] * count
    for income, count in zip(histogram.bin_centers, histogram.bin_counts)
)

# Find revenue-neutral reformed rate
optimal_rate, achieved = optimize_additional_rate_for_revenue(
    baseline_revenue, histogram, top_percentile_income=201000
)

print(f"Current system: 45% rate (starts at £125,140)")
print(f"Reformed system: {optimal_rate*100:.1f}% rate (starts at £100,000)")
print(f"Revenue difference: £{achieved - baseline_revenue:,.0f}")

# Create reformed calculator
reformed = UKTaxCalculatorReformed(additional_rate=optimal_rate)

# Compare at £110k
income = 110000
print(f"\nAt £{income:,}:")
print(f"  Current marginal: {current.calculate_marginal_rate(income):.1f}%")
print(f"  Reformed marginal: {reformed.calculate_marginal_rate(income):.1f}%")
```

### Available Calculators

```python
from uktax import (
    UKTaxCalculatorPre2010,    # Before PA taper (no trap)
    UKTaxCalculator2010,        # 50% additional rate era
    UKTaxCalculator2013,        # 45% additional rate era
    UKTaxCalculator2023,        # Current system (trap at £100k-£125k)
    UKTaxCalculatorReformed     # No PA taper (eliminates trap)
)
```

## Project Structure

```
uktax/
├── src/uktax/
│   ├── income_data.py           # Income distribution classes
│   ├── uk_tax_calculator.py     # Tax calculators (5 historical periods)
│   ├── visualizations.py        # Plotting utilities
│   └── scripts/                 # CLI entry points
├── tests/                       # Test suite
├── article.md                   # Full analysis and reform proposals
├── generate_article_analysis.py # Generates all plots and data
└── README.md                    # This file
```

## Key Findings

### Current System (2023-Present)
- Personal allowance: £12,570 (tapered above £100k, gone by £125,140)
- Basic rate: 20% (£12,571-£50,270)
- Higher rate: 40% (£50,271-£125,140)
- Additional rate: 45% (above £125,140)
- **60% trap zone**: £100,000-£125,140

### Revenue-Neutral Reform
- Remove PA taper (everyone keeps full £12,570)
- Move higher rate threshold to £100,000
- Increase additional rate to **46.9%** (from 45%)
- **Result**: Trap eliminated, revenue unchanged

**Impact** (using 2022/23 income distribution):
- Winners: 2,383 people (2.4%) save £386/year average
- Losers: 1,610 people (1.6%) pay £572/year more average
- Unchanged: 96,006 people (96.0%)

### Alternative: 45% Fixed Rate Reform
- Same as above but keep 45% rate
- Revenue decrease: £4.0M (0.5% of total)
- Winners: 3,993 people (4.0%) save £1,014/year average
- Losers: **0 people** (nobody pays more!)

## Methodology Notes

### Top 1% Income Assumption

HMRC data provides income distribution from 1st-99th percentile (up to £201,000). For the top 1%, we conservatively assume they earn **at least** the 99th percentile value.

**Why this matters**: The assumption affects optimal rate calculations:
- Conservative (£201k): 46.9% optimal rate ✅
- Optimistic (£231k, +15%): 40.9% optimal rate ❌ (likely revenue shortfall)

**Difference**: 6 percentage points! We use the conservative approach to ensure actual revenue neutrality.

See [article.md](article.md) for full details.

## Testing

Run comprehensive validation:
```bash
python tests/test_comprehensive_validation.py
```

63 tests covering:
- Marginal rate accuracy
- Effective rate consistency
- PA taper correctness
- Revenue optimization
- Monotonicity (tax increases with income)
- Edge cases

## Dependencies

- numpy >= 1.20.0
- matplotlib >= 3.3.0
- scipy >= 1.7.0
- attrs >= 21.0.0

## License

See LICENSE file.

## Author

Peter Wurmsdobler <peter@wurmsdobler.org>

## Further Reading

- [article.md](article.md) - Comprehensive analysis with historical evolution and reform proposals
