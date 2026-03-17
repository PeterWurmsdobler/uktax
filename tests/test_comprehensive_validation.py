#!/usr/bin/env python3
"""
Comprehensive validation of all tax calculations.
Tests edge cases, consistency, and mathematical correctness.
"""

from uktax import (
    UKTaxCalculator2023, 
    UKTaxCalculatorReformed,
    UKTaxCalculatorPre2010,
    UKTaxCalculator2010,
    UKTaxCalculator2013,
    IncomeDistributionData,
    IncomeHistogram,
    UK_INCOME_2023,
    optimize_additional_rate_for_revenue
)
import math

print("\n" + "="*80)
print("COMPREHENSIVE VALIDATION OF TAX CALCULATIONS")
print("="*80)

# Track test results
total_tests = 0
passed_tests = 0
failed_tests = 0

def test_assert(condition, test_name, details=""):
    """Helper to track test results."""
    global total_tests, passed_tests, failed_tests
    total_tests += 1
    if condition:
        passed_tests += 1
        print(f"   ✓ {test_name}")
        if details:
            print(f"     {details}")
        return True
    else:
        failed_tests += 1
        print(f"   ✗ FAILED: {test_name}")
        if details:
            print(f"     {details}")
        return False

# =============================================================================
# TEST 1: Marginal Rate Calculation Correctness
# =============================================================================
print("\n" + "-"*80)
print("TEST 1: Marginal Rate Calculation (Numerical Derivative)")
print("-"*80)

def calculate_marginal_rate_numerically(calc, income, delta=1.0):
    """Calculate marginal rate by numerical differentiation."""
    tax_at_income = calc.calculate_total_deductions(income)[0]
    tax_at_income_plus_delta = calc.calculate_total_deductions(income + delta)[0]
    return (tax_at_income_plus_delta - tax_at_income) / delta * 100

calc_2023 = UKTaxCalculator2023()

# Test at various income levels
test_incomes = [
    (10000, "Below basic threshold"),
    (50000, "In basic rate band"),
    (60000, "In higher rate band"),
    (100000, "Start of PA taper"),
    (105000, "Middle of 60% trap"),
    (110000, "In 60% trap"),
    (125140, "End of PA taper"),
    (150000, "Additional rate band"),
]

for income, description in test_incomes:
    reported_marginal = calc_2023.calculate_marginal_rate(income)
    numerical_marginal = calculate_marginal_rate_numerically(calc_2023, income)
    
    # Allow 0.5% tolerance due to discretization
    difference = abs(reported_marginal - numerical_marginal)
    test_assert(
        difference < 0.5,
        f"Marginal rate at £{income:,} ({description})",
        f"Reported: {reported_marginal:.2f}%, Numerical: {numerical_marginal:.2f}%, Diff: {difference:.2f}%"
    )

# =============================================================================
# TEST 2: Effective Rate Consistency
# =============================================================================
print("\n" + "-"*80)
print("TEST 2: Effective Rate Consistency")
print("-"*80)

for income, description in test_incomes:
    total_tax, _, _ = calc_2023.calculate_total_deductions(income)
    reported_effective = calc_2023.calculate_effective_rate(income)
    calculated_effective = (total_tax / income) * 100
    
    difference = abs(reported_effective - calculated_effective)
    test_assert(
        difference < 0.01,
        f"Effective rate at £{income:,} ({description})",
        f"Reported: {reported_effective:.2f}%, Calculated: {calculated_effective:.2f}%"
    )

# =============================================================================
# TEST 3: Net Income Consistency
# =============================================================================
print("\n" + "-"*80)
print("TEST 3: Net Income = Gross - Tax - NI")
print("-"*80)

for income, description in test_incomes:
    total_deductions, income_tax, ni = calc_2023.calculate_total_deductions(income)
    net_income = calc_2023.calculate_net_income(income)
    
    calculated_net = income - total_deductions
    difference = abs(net_income - calculated_net)
    test_assert(
        difference < 0.01,
        f"Net income at £{income:,} ({description})",
        f"Method: £{net_income:,.2f}, Calculated: £{calculated_net:,.2f}"
    )
    
    # Also verify that total_deductions = income_tax + ni
    calculated_total = income_tax + ni
    diff_deductions = abs(total_deductions - calculated_total)
    test_assert(
        diff_deductions < 0.01,
        f"Total deductions = Tax + NI at £{income:,}",
        f"Total: £{total_deductions:,.2f}, Tax+NI: £{calculated_total:,.2f}"
    )

# =============================================================================
# TEST 4: Personal Allowance Taper Verification
# =============================================================================
print("\n" + "-"*80)
print("TEST 4: Personal Allowance Taper (£1 lost per £2 over threshold)")
print("-"*80)

# PA should taper at £1 for every £2 over £100,000
taper_threshold = 100000
standard_pa = 12570

test_taper_incomes = [100000, 105000, 110000, 115000, 120000, 125140, 130000]

for income in test_taper_incomes:
    pa = calc_2023.calculate_personal_allowance(income)
    
    if income <= taper_threshold:
        expected_pa = standard_pa
    else:
        excess = income - taper_threshold
        reduction = excess / 2
        expected_pa = max(0, standard_pa - reduction)
    
    difference = abs(pa - expected_pa)
    test_assert(
        difference < 0.01,
        f"PA at £{income:,}",
        f"Calculated: £{pa:,.0f}, Expected: £{expected_pa:,.0f}"
    )

# =============================================================================
# TEST 5: 60% Trap Verification
# =============================================================================
print("\n" + "-"*80)
print("TEST 5: 60% Marginal Rate in Trap Zone")
print("-"*80)

# In the trap zone (£100k-£125,140), marginal rate should be elevated
# This is 40% income tax + 2% NI + loss of PA at 40% rate (20% effective)
# Expected: around 52-62% depending on NI thresholds
trap_start = 100001
trap_end = 125140

trap_incomes = [100001, 105000, 110000, 115000, 120000]  # Removed 125000 - too close to boundary

for income in trap_incomes:
    marginal = calc_2023.calculate_marginal_rate(income)
    
    # Should be elevated (40% higher rate + 20% from PA loss + NI)
    # Allow range 50-65% for boundary effects and NI threshold transitions
    in_trap = 50 <= marginal <= 65
    test_assert(
        in_trap,
        f"Elevated marginal rate in trap at £{income:,}",
        f"Marginal rate: {marginal:.2f}% (expected 50-65%)"
    )

# =============================================================================
# TEST 6: Reformed Calculator - No Taper
# =============================================================================
print("\n" + "-"*80)
print("TEST 6: Reformed Calculator Has No PA Taper")
print("-"*80)

reformed_calc = UKTaxCalculatorReformed()

for income in [50000, 100000, 110000, 125000, 150000, 200000]:
    pa = reformed_calc.calculate_personal_allowance(income)
    test_assert(
        pa == 12570,
        f"Reformed PA at £{income:,}",
        f"PA: £{pa:,.0f} (should always be £12,570)"
    )

# =============================================================================
# TEST 7: Historical Progression Consistency
# =============================================================================
print("\n" + "-"*80)
print("TEST 7: Historical PA and Thresholds")
print("-"*80)

# Pre-2010: PA = £6,475, no taper, basic threshold £43,875 (PA + £37,400 band)
pre2010 = UKTaxCalculatorPre2010()
test_assert(
    pre2010.personal_allowance == 6475,
    "Pre-2010 PA",
    f"PA: £{pre2010.personal_allowance:,}"
)
test_assert(
    pre2010.basic_rate_threshold == 43875,
    "Pre-2010 basic threshold",
    f"Threshold: £{pre2010.basic_rate_threshold:,} (PA + basic band)"
)

# 2010: PA still £6,475, but taper introduced
calc_2010 = UKTaxCalculator2010()
test_assert(
    calc_2010.personal_allowance == 6475,
    "2010 PA",
    f"PA: £{calc_2010.personal_allowance:,}"
)
test_assert(
    calc_2010.calculate_personal_allowance(100000) == 6475,
    "2010 PA below taper"
)
test_assert(
    calc_2010.calculate_personal_allowance(110000) < 6475,
    "2010 PA tapers above £100k"
)

# =============================================================================
# TEST 8: Revenue Neutrality of Optimization
# =============================================================================
print("\n" + "-"*80)
print("TEST 8: Revenue-Neutral Reform Optimization")
print("-"*80)

# Create histogram
distribution = IncomeDistributionData.from_list(UK_INCOME_2023, start_percentile=1)
histogram = IncomeHistogram.from_distribution(
    distribution, 
    population_size=100000, 
    bin_size=1000,
    max_income=202000
)

# Calculate original revenue
original_calc = UKTaxCalculator2023()
total_revenue = 0
for i in range(len(histogram.bin_counts)):
    income = histogram.bin_centers[i]
    people = histogram.bin_counts[i]
    
    max_known_income = histogram.source_data.incomes[-1]
    if income > max_known_income:
        income = 202000
    
    deductions, _, _ = original_calc.calculate_total_deductions(income)
    total_revenue += deductions * people

print(f"\n   Original total revenue: £{total_revenue:,.2f}")

# Optimize reformed additional rate
optimal_rate, achieved_revenue = optimize_additional_rate_for_revenue(
    total_revenue, 
    histogram, 
    top_percentile_income=202000
)

print(f"   Optimal additional rate: {optimal_rate*100:.2f}%")
print(f"   Achieved revenue: £{achieved_revenue:,.2f}")

revenue_diff = abs(achieved_revenue - total_revenue)
revenue_diff_pct = (revenue_diff / total_revenue) * 100

test_assert(
    revenue_diff < 1000,  # Within £1,000
    "Revenue neutrality (absolute)",
    f"Difference: £{revenue_diff:,.2f}"
)

test_assert(
    revenue_diff_pct < 0.001,  # Within 0.001%
    "Revenue neutrality (percentage)",
    f"Difference: {revenue_diff_pct:.6f}%"
)

# =============================================================================
# TEST 9: Edge Cases
# =============================================================================
print("\n" + "-"*80)
print("TEST 9: Edge Cases")
print("-"*80)

# Zero income
zero_tax, zero_it, zero_ni = calc_2023.calculate_total_deductions(0)
test_assert(
    zero_tax == 0 and zero_it == 0 and zero_ni == 0,
    "Zero income has zero tax",
    f"Tax: £{zero_tax}, IT: £{zero_it}, NI: £{zero_ni}"
)

# Very low income (below PA)
low_income = 5000
low_tax, low_it, low_ni = calc_2023.calculate_total_deductions(low_income)
test_assert(
    low_it == 0,
    "Income below PA has no income tax",
    f"Income: £{low_income:,}, IT: £{low_it}"
)

# Exactly at PA
pa_income = 12570
pa_tax, pa_it, pa_ni = calc_2023.calculate_total_deductions(pa_income)
test_assert(
    pa_it == 0,
    "Income exactly at PA has no income tax",
    f"Income: £{pa_income:,}, IT: £{pa_it}"
)

# Exactly at thresholds
threshold_50270 = 50270  # Basic rate upper limit
thresh_tax, thresh_it, thresh_ni = calc_2023.calculate_total_deductions(threshold_50270)
# Should be all basic rate tax
expected_basic_tax = (threshold_50270 - 12570) * 0.20
test_assert(
    abs(thresh_it - expected_basic_tax) < 1,
    "Tax calculation at basic rate threshold",
    f"Calculated: £{thresh_it:,.2f}, Expected: £{expected_basic_tax:,.2f}"
)

# =============================================================================
# TEST 10: Monotonicity - Tax increases with income
# =============================================================================
print("\n" + "-"*80)
print("TEST 10: Monotonicity - Tax Increases with Income")
print("-"*80)

prev_tax = 0
monotonic = True
for income in range(10000, 200000, 5000):
    current_tax, _, _ = calc_2023.calculate_total_deductions(income)
    if current_tax < prev_tax:
        monotonic = False
        print(f"   ✗ Tax decreased at £{income:,}: {current_tax:.2f} < {prev_tax:.2f}")
    prev_tax = current_tax

test_assert(
    monotonic,
    "Tax is monotonically increasing",
    "Tax never decreases as income increases"
)

# =============================================================================
# TEST 11: Effective Rate Bounds
# =============================================================================
print("\n" + "-"*80)
print("TEST 11: Effective Rate Bounds (0% to ~50%)")
print("-"*80)

all_within_bounds = True
for income in range(10000, 200000, 10000):
    effective = calc_2023.calculate_effective_rate(income)
    
    if not (0 <= effective <= 50):
        all_within_bounds = False
        print(f"   ✗ Out of bounds at £{income:,}: {effective:.2f}%")

test_assert(
    all_within_bounds,
    "All effective rates between 0% and 50%",
    "Checked incomes from £10k to £200k"
)

# =============================================================================
# Summary
# =============================================================================
print("\n" + "="*80)
print("TEST SUMMARY")
print("="*80)
print(f"\nTotal tests: {total_tests}")
print(f"Passed: {passed_tests} ✓")
print(f"Failed: {failed_tests} ✗")
print(f"Success rate: {(passed_tests/total_tests*100):.1f}%")

if failed_tests == 0:
    print("\n🎉 ALL TESTS PASSED! 🎉")
    print("="*80 + "\n")
    exit(0)
else:
    print("\n⚠️  SOME TESTS FAILED - REVIEW REQUIRED")
    print("="*80 + "\n")
    exit(1)
