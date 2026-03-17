#!/usr/bin/env python3
"""Quick test of the plot-reform functionality."""

from uktax import (IncomeDistributionData, IncomeHistogram, UK_INCOME_2023,
                   UKTaxCalculator2023, UKTaxCalculatorReformed,
                   optimize_additional_rate_for_revenue)

print("\n" + "="*70)
print("Testing Tax Reform Optimization")
print("="*70)

# Create distribution and histogram
print("\n1. Creating income distribution and histogram...")
distribution = IncomeDistributionData.from_list(
    UK_INCOME_2023, 
    start_percentile=1, 
    year="2023"
)

histogram = IncomeHistogram.from_distribution(
    distribution,
    population_size=100000,
    bin_size=1000,
    max_income=202000
)
print(f"   Population: {histogram.population_size:,}")
print(f"   Mean income: £{histogram.mean_income:,.0f}")

# Calculate revenue with original calculator
print("\n2. Calculating revenue with ORIGINAL tax system...")
original_calculator = UKTaxCalculator2023()

total_revenue = 0
for i in range(len(histogram.bin_counts)):
    income = histogram.bin_centers[i]
    people = histogram.bin_counts[i]
    
    max_known_income = histogram.source_data.incomes[-1]
    if income > max_known_income:
        # Conservative assumption: top 1% earn at least 99th percentile
        income = max_known_income
    
    deductions, _, _ = original_calculator.calculate_total_deductions(income)
    total_revenue += deductions * people

print(f"   Original additional rate: {original_calculator.additional_rate*100:.1f}%")
print(f"   Total revenue: £{total_revenue:,.2f}")

# Optimize additional rate for reformed calculator
print("\n3. Optimizing REFORMED tax system...")
print("   Finding additional rate that generates same revenue...")

# Use conservative assumption: top 1% earn at least 99th percentile
max_known_income = histogram.source_data.incomes[-1]
optimal_rate, achieved_revenue = optimize_additional_rate_for_revenue(
    total_revenue, 
    histogram, 
    max_known_income
)

print(f"\n   ✓ Optimal additional rate: {optimal_rate*100:.2f}%")
print(f"   ✓ Achieved revenue: £{achieved_revenue:,.2f}")
print(f"   ✓ Target revenue: £{total_revenue:,.2f}")
print(f"   ✓ Difference: £{abs(achieved_revenue - total_revenue):,.2f}")
print(f"   ✓ Match: {(achieved_revenue/total_revenue*100):.6f}%")

print("\n" + "="*70)
print("Test completed successfully!")
print("="*70 + "\n")
