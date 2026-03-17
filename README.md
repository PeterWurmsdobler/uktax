# UK Tax and Income Distribution Analysis

A Python package for analyzing UK tax rates and income distribution with a focus on identifying and fixing the **60% marginal rate trap** in the current UK tax system.

## The 60% Marginal Rate Trap Problem

The UK tax system has a hidden quirk that creates an **effective 60% marginal tax rate** for incomes between **£100,000 and £116,760**. This happens because:

1. The personal allowance (£12,570) is gradually withdrawn at a rate of £1 for every £2 earned above £100,000
2. This withdrawal creates an implicit 20% tax on top of the 40% higher rate
3. Combined with National Insurance (≈2%), the total marginal rate reaches approximately **60%**

**Example**: Someone earning £110,000 has a marginal rate higher than someone earning £200,000 (who pays only 47%). This creates a perverse incentive where earning an additional £10,000 only nets you £4,000.

This package provides tools to:
- **Visualize** this trap in the current system
- **Analyze** the revenue impact of removing it
- **Calculate** what additional rate adjustment is needed for revenue neutrality

## Installation

### From source

```bash
cd uktax
pip install -e .
```

### With development dependencies

```bash
pip install -e ".[dev]"
```

## Command-Line Interface

The package provides a unified `uktax` command with four subcommands for different analyses.

### Overview
```bash
uktax --help  # Show all available commands
```

### `uktax revenue` - Calculate Tax Revenue

**Purpose**: Calculates total tax revenue from the UK income distribution using the classic tax system.

**Use Case**: Understanding how much revenue the current tax system generates from a given population.

**What it does**:
- Takes UK income distribution data (1st-99th percentile)
- Creates a population histogram with specified population size
- Applies classic UK tax calculator (with PA tapering) to each income bracket
- Computes total income tax, National Insurance, and combined revenue
- Shows average tax per person and effective tax rate

**Example Output**:
```
Total revenue: £78,803,805 (£788 per person)
  Income tax: £61,974,251 (£620 per person)
  National Insurance: £16,829,553 (£168 per person)
Total gross income: £269,999,942
Effective tax rate: 29.2%
```

**Usage**:
```bash
# Basic usage with defaults (100k population, £1k bins)
uktax revenue

# Larger population for more accuracy
uktax revenue --population 1000000

# Custom bin size for finer granularity
uktax revenue --bin-size 500 --max-income 250000
```

**Options**:
- `--population` (default: 100000): Population size to simulate
- `--bin-size` (default: 1000): Income bin width in pounds
- `--max-income` (default: 202000): Maximum income threshold
- `--top-percentile-income` (default: 202000): Assumed income for top 1%

### `uktax plot-income` - Visualize Income Distribution

**Purpose**: Creates visual representations of the UK income distribution.

**Use Case**: Understanding income inequality and the distribution shape before applying tax calculations.

**What it does**:
- Plots cumulative distribution curve (percentile → income)
- Shows population histogram with number of people in each income bracket
- Annotates key percentiles (25th, 50th/median, 75th, 90th, 95th, 99th)
- Displays mean income
- Highlights the top 1% separately (data beyond £201k is unknown)

**Usage**:
```bash
# Basic usage
uktax plot-income

# Larger population for smoother histogram
uktax plot-income --population 200000 --bin-size 2000
```

**Options**:
- `--population` (default: 100000): Population size to simulate
- `--bin-size` (default: 1000): Income bin width in pounds
- `--max-income` (default: 202000): Maximum income threshold

**Visual Output**: 2-panel figure showing cumulative distribution and histogram.

### `uktax plot-tax` - Visualize Tax Rates & Deductions

**Purpose**: Visualizes how the classic UK tax system (with PA tapering) affects different income levels, making the 60% trap visible.

**Use Case**: Identifying problematic marginal rates and understanding where tax inefficiencies occur.

**What it does**:
- **Top panel**: Shows gross income vs net income after tax/NI
- **Bottom panel**: Shows marginal tax rate curve across income range
- **Highlights the 60% trap**: Annotates the £100k-£125k region where marginal rate spikes
- Compares across income bands: basic (20%), higher (40%), additional (45%)

**Visual insight**: You'll see the marginal rate jump from 40% to ~60% at £100k, then drop back to ~47% at £125k+ — this anomaly is the core problem.

**Usage**:
```bash
# Basic usage (0 to £160k)
uktax plot-tax

# Extended range to see high earners
uktax plot-tax --max-income-range 200000 --income-step 500
```

**Options**:
- `--max-income-range` (default: 160000): Maximum income for visualization
- `--income-step` (default: 1000): Income increment for calculations (smaller = smoother curves)

**Visual Output**: 2-panel figure showing income vs deductions and marginal rate curve.

### `uktax plot-reform` - Analysis of Reformed Tax System

**Purpose**: Investigates whether we can **eliminate the 60% trap** and visualizes the impact under different reform scenarios.

**Use Case**: Policy analysis — understanding the trade-offs of removing PA tapering with different additional rate choices.

**What it does**:
1. **Calculates baseline revenue** using classic system (45% additional rate with PA tapering)
2. **Applies chosen reform scenario**:
   - **Revenue-neutral**: Optimizes additional rate for same revenue (scipy's Brent method)
   - **Fixed-rate**: Uses specified additional rate (default 45%, customizable)
3. **Creates 4-panel comparison visualization**:
   - Panel 1: Marginal rates (classic vs reformed)
   - Panel 2: Effective tax rates across incomes
   - Panel 3: Tax difference (reformed minus classic)
   - Panel 4: Winners and losers scatter plot

**Key Finding**: By removing the personal allowance taper and setting the additional rate threshold at £100,000 (where the trap begins), the reformed system eliminates the 60% trap. Two main approaches:

**1. Revenue-Neutral (43.86% additional rate)**:
- Additional rate is **lower than current 45%**
- Perfect revenue match (£0 difference)
- Winners: 1,067 people (1.1%) save £1,306/year on average
- Losers: 2,925 people (2.9%) pay £476/year more on average
- Unchanged: 96,006 people (96%)

**2. Fixed-Rate at 45% (same as current)**:
- Simple to communicate (same rate as current top rate)
- Small revenue gain: £2.4M (+0.30%)
- Winners: 1,067 people (1.1%) save £1,213/year on average
- Losers: 2,925 people (2.9%) pay £1,257/year more on average
- Unchanged: 96,006 people (96%)

**Usage**:
```bash
# Default: Revenue-neutral scenario (optimized rate)
uktax plot-reform

# Fixed-rate scenario with default 45%
uktax plot-reform --scenario fixed-rate

# Fixed-rate with custom percentage (e.g., 40%)
uktax plot-reform --scenario fixed-rate --fixed-rate-percent 40

# Larger population for more accurate optimization
uktax plot-reform --population 500000 --max-income-range 200000
```

**Options**:
- `--scenario` (default: 'revenue-neutral'): Choose 'revenue-neutral' (optimize rate) or 'fixed-rate' (specify rate)
- `--fixed-rate-percent` (default: 45.0): Additional rate percentage for fixed-rate scenario
- `--population` (default: 100000): Population size for revenue calculation
- `--bin-size` (default: 1000): Income bin width
- `--max-income` (default: 202000): Maximum income threshold
- `--top-percentile-income` (default: 202000): Assumed income for top 1%
- `--max-income-range` (default: 160000): Maximum income for visualization
- `--income-step` (default: 1000): Income increment for plotting

**Rate Comparison Table**:

| Additional Rate | Revenue Change | Winners (avg saving) | Losers (avg cost) | Notes |
|-----------------|----------------|----------------------|-------------------|-------|
| 40% | -£8.1M (-1.0%) | 3,697 (£2,205/yr) | 296 (£207/yr) | Large revenue loss |
| 43.86% | £0 (0.0%) | 1,067 (£1,306/yr) | 2,925 (£475/yr) | **Revenue neutral** |
| 45% | +£2.4M (+0.3%) | 1,067 (£1,213/yr) | 2,925 (£1,257/yr) | Same as current rate |
| 47% | +£6.6M (+0.8%) | 1,067 (£1,052/yr) | 2,925 (£2,630/yr) | Moderate gain |
| 50% | +£12.9M (+1.6%) | 1,067 (£809/yr) | 2,925 (£4,689/yr) | Large gain, costly |

All rates eliminate the 60% trap and maintain constant personal allowance.

**Console Output Example (Revenue-Neutral)**:
```
TAX REFORM ANALYSIS: Revenue-Neutral Reform

Original system (with PA taper):
  Total revenue: £788,038,054

Finding additional rate that matches original revenue...
  Optimal additional rate: 43.86%
  Achieved revenue: £788,038,054
  Revenue difference: £0.00

Winners (pay less): 1,067 people (avg. saving: £1,306/year)
Losers (pay more): 2,925 people (avg. cost: £476/year)
Unchanged: 96,006 people
```

**Console Output Example (Fixed 45%)**:
```
TAX REFORM ANALYSIS: Fixed 45.0% Rate Reform

Original system (with PA taper):
  Total revenue: £788,038,054

Using fixed additional rate: 45.0%
  Reformed revenue: £790,420,615
  Revenue GAIN: £2,382,561 (0.30%)

Winners (pay less): 1,067 people (avg. saving: £1,213/year)
Losers (pay more): 2,925 people (avg. cost: £1,257/year)
Unchanged: 96,006 people
```

**Visual Output**: 4-panel figure comparing classic and reformed systems.

### Running Commands Directly

You can also run commands as Python modules:
```bash
python -m uktax.main revenue
python -m uktax.main plot-income
python -m uktax.main plot-tax
python -m uktax.main plot-reform
```

## Python API Usage

### Income Distribution Analysis

```python
from uktax import IncomeDistributionData, IncomeHistogram, UK_INCOME_2023

# Create distribution from UK 2023 data
distribution = IncomeDistributionData.from_list(UK_INCOME_2023, start_percentile=1)

# Query income at specific percentile
median_income = distribution.get_income_at_percentile(50)  # £50,000
p90_income = distribution.get_income_at_percentile(90)      # £120,000

# Create histogram for population analysis
histogram = IncomeHistogram.from_distribution(
    distribution, 
    population_size=100000,  # 100k people
    bin_size=1000            # £1k bins
)

print(f"Mean income: £{histogram.mean_income:,.0f}")
print(f"Median income: £{histogram.median_income:,.0f}")
print(f"Number of bins: {len(histogram.bin_counts)}")
```

### Tax Calculations with Classic System

```python
from uktax import UKTaxCalculatorClassic

calculator = UKTaxCalculatorClassic()

# Calculate for single income
income = 110000  # In the 60% trap zone
total_tax, income_tax, ni = calculator.calculate_total_deductions(income)
net_income = calculator.calculate_net_income(income)
marginal_rate = calculator.calculate_marginal_rate(income)

print(f"Gross: £{income:,}")
print(f"Income tax: £{income_tax:,.0f}")
print(f"National Insurance: £{ni:,.0f}")
print(f"Total deductions: £{total_tax:,.0f}")
print(f"Net income: £{net_income:,.0f}")
print(f"Marginal rate: {marginal_rate:.1f}%")  # Will show ~60%
```

### Comparing Classic vs Reformed Systems

```python
from uktax import (
    UKTaxCalculatorClassic, 
    UKTaxCalculatorReformed,
    IncomeHistogram,
    optimize_additional_rate_for_revenue
)

# Setup income distribution
histogram = IncomeHistogram.from_distribution(
    distribution, 
    population_size=100000, 
    bin_size=1000
)

# Calculate baseline revenue with classic system
classic_calc = UKTaxCalculatorClassic()
baseline_revenue = sum(
    classic_calc.calculate_total_deductions(income)[0] * count
    for income, count in zip(histogram.bin_centers, histogram.bin_counts)
)
print(f"Baseline revenue: £{baseline_revenue:,.0f}")

# Find optimal additional rate for reformed system
optimal_rate, achieved_revenue = optimize_additional_rate_for_revenue(
    target_revenue=baseline_revenue,
    histogram=histogram,
    top_percentile_income=202000
)

print(f"\nClassic additional rate: {classic_calc.additional_rate*100:.1f}% (starts at £125,140)")
print(f"Reformed additional rate: {optimal_rate*100:.2f}% (starts at £100,000)")
print(f"Revenue difference: £{achieved_revenue - baseline_revenue:,.0f}")

# Create reformed calculator and compare
reformed_calc = UKTaxCalculatorReformed(additional_rate=optimal_rate)

# Compare at £110k (peak of 60% trap)
income = 110000
classic_marginal = classic_calc.calculate_marginal_rate(income)
reformed_marginal = reformed_calc.calculate_marginal_rate(income)

print(f"\nMarginal rates at £{income:,}:")
print(f"  Classic: {classic_marginal:.1f}%")   # ~60%
print(f"  Reformed: {reformed_marginal:.1f}%")  # ~43.8%
print(f"  Improvement: {classic_marginal - reformed_marginal:.1f}pp")
```

### Visualization

```python
from uktax import IncomeDistributionVisualizer, TaxVisualization
import matplotlib.pyplot as plt

# Visualize income distribution
visualizer = IncomeDistributionVisualizer()
fig, axes = visualizer.plot_cumulative_and_histogram(distribution, histogram)
plt.savefig('income_distribution.png', dpi=150, bbox_inches='tight')
plt.show()

# Visualize tax rates (shows 60% trap)
tax_viz = TaxVisualization(classic_calc)
fig, axes = tax_viz.plot_tax_analysis()
plt.savefig('tax_analysis.png', dpi=150, bbox_inches='tight')
plt.show()
```

## Architecture

### Project Structure

```
uktax/
├── pyproject.toml              # Package configuration
├── README.md                   # This file
├── src/
│   └── uktax/
│       ├── __init__.py               # Package exports
│       ├── income_data.py            # Income distribution data classes
│       ├── uk_tax_calculator.py      # Tax calculation engine with class hierarchy
│       ├── visualizations.py         # Visualization classes
│       └── main.py                   # Unified CLI entry point
└── tests/
    ├── test_reform.py                # Revenue optimization tests
    ├── demo_marginal_rates.py        # Marginal rate comparison demo
    └── test_abstract_base.py         # Abstract base class tests
```

### Core Classes

#### `income_data.py` - Income Distribution

- **`IncomeDistributionData`**: Percentile-based income data
  - Uses `attrs` for type-safe data classes
  - Interpolates income at any percentile
  - Finds percentile for any income level
  
- **`IncomeHistogram`**: Population histogram
  - Converts percentile data to population bins
  - Calculates mean and median income
  - Handles arbitrary bin sizes and population sizes
  
- **`UK_INCOME_2023`**: Real UK income data (1st-99th percentile from 2023)

#### `uk_tax_calculator.py` - Tax Calculation Engine

- **`UKTaxCalculatorBase`**: Abstract base class (ABC)
  - Common tax parameters (rates, thresholds, NI rates)
  - Shared methods: `calculate_income_tax()`, `calculate_ni()`, `calculate_marginal_rate()`, etc.
  - Abstract method: `calculate_personal_allowance()` (must be implemented by subclasses)
  - Cannot be instantiated directly — enforces implementation contract
  
- **`UKTaxCalculatorClassic`**: Current UK tax system
  - Implements PA tapering: £12,570 reduced by £1 for every £2 above £100k
  - **Creates the 60% trap** in £100k-£125k range
  - Default additional rate: 45%
  - Represents 2024/25-2025/26 tax year rules
  
- **`UKTaxCalculator`**: Alias for `UKTaxCalculatorClassic` (backwards compatibility)
  
- **`UKTaxCalculatorReformed`**: Alternative system without PA tapering
  - Personal allowance stays constant (£12,570) at all income levels
  - **Eliminates the 60% trap**
  - Configurable additional rate (defaults to 45%, but use optimization to find revenue-neutral rate)
  
- **`optimize_additional_rate_for_revenue()`**: Optimization function
  - Uses scipy's Brent method (root finding with bounded interval)
  - Finds additional rate that matches target revenue
  - Returns optimal rate and achieved revenue
  - Convergence tolerance: 0.1% of target revenue

#### `visualizations.py` - Plotting

- **`IncomeDistributionVisualizer`**: Income distribution plots
  - Cumulative distribution curves
  - Population histograms with top 1% handling
  - Automatic annotation of key percentiles
  
- **`TaxVisualization`**: Tax analysis plots
  - Income vs deductions comparison
  - Marginal and effective tax rate curves
  - Automatic annotation of anomalies (e.g., 60% trap marker)

## Technical Details

### Tax Parameters (2024/25 - 2025/26)

**Income Tax**:
- Personal allowance: £12,570 (tapered above £100k in classic system)
- Basic rate: 20% on £12,571 - £50,270
- Higher rate: 40% on £50,271 - £125,140 (classic) or £50,271 - £100,000 (reformed)
- Additional rate: 45% on £125,140+ (classic) or 43.86% on £100,000+ (reformed, revenue-neutral)

**National Insurance**:
- 0% on £0 - £12,570
- 8% on £12,571 - £50,270
- 2% on £50,270+

**Personal Allowance Tapering** (Classic system only):
- Reduced by £1 for every £2 earned above £100,000
- Fully withdrawn at £125,140 (£12,570 × 2 + £100,000)
- The 60% trap ends at £116,760 when taxable income reaches the additional rate threshold

### The Math Behind the 60% Trap

For someone earning between £100k and £125k:
- Base higher rate: **40%**
- Loss of personal allowance: **20%** (£1 PA lost per £2 earned → £0.20 tax per £1 earned)
- National Insurance: **≈2%**
- **Total marginal rate: ≈62%**

This means earning an extra £10,000 in this range only yields £3,800 net.

### Revenue Neutrality Optimization

The `optimize_additional_rate_for_revenue()` function uses **Brent's method** to find the root of:

$$f(r) = \text{Revenue}_{\text{reformed}}(r) - \text{Revenue}_{\text{target}}$$

Where $r$ is the additional rate. The method:
1. Brackets the solution between 0.40 (40%) and 0.70 (70%)
2. Uses inverse quadratic interpolation for fast convergence
3. Stops when revenue matches within 0.1% of target

**Result**: Reformed system with 43.86% additional rate (starting at £100,000, where the trap begins) generates the same revenue while eliminating the 60% trap. Remarkably, the additional rate is **lower than the current 45%** because it starts earlier. Alternative rates (40%-50%) provide policy flexibility for different revenue and distributional objectives.

## Dependencies

- **numpy** (≥1.20.0): Numerical computations, array operations
- **matplotlib** (≥3.3.0): Plotting and visualization
- **attrs** (≥21.0.0): Type-safe data classes with validation
- **scipy** (≥1.7.0): Optimization algorithms (Brent method)

Install all dependencies:
```bash
pip install numpy matplotlib attrs scipy
```

Or install the package with dependencies:
```bash
pip install -e .
```

## Key Features

✓ **Identifies tax system flaws**: Visualizes the 60% marginal rate trap  
✓ **Proposes evidence-based reform**: Shows removal requires only 1.3pp rate increase  
✓ **Revenue-neutral analysis**: Maintains total tax revenue while improving fairness  
✓ **Clean architecture**: Abstract base class ensures consistent calculator implementations  
✓ **Flexible and extensible**: Easy to add new tax rules or income distributions  
✓ **Professional visualizations**: Automatically annotated with insights  
✓ **Command-line and Python API**: Use as tool or library  
✓ **Type-safe data classes**: Using `attrs` for structured data with validation  

## Notes

- Tax rates based on UK 2024/25 - 2025/26 tax year (Rest of UK, excluding Scotland)
- Income data from 2023 UK distribution (percentiles 1-99)
- Top 1% handled separately (data beyond £201k unavailable; conservatively assumed at £202k)
- Personal allowance tapering creates the 60% trap in classic system only
- Reformed system eliminates tapering but requires higher additional rate for revenue neutrality
- All calculations assume taxable income (after pension contributions, etc.)
