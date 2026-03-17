#!/usr/bin/env python3
"""Test winners and losers calculation."""

from uktax import (UKTaxCalculator2023, UKTaxCalculatorReformed, 
                   optimize_additional_rate_for_revenue,
                   IncomeDistributionData, IncomeHistogram, UK_INCOME_2023)

# Create histogram
distribution = IncomeDistributionData.from_list(UK_INCOME_2023, start_percentile=1)
histogram = IncomeHistogram.from_distribution(distribution, population_size=100000, bin_size=1000)

# Calculate baseline revenue (matching main.py method with top percentile handling)
original_calc = UKTaxCalculator2023()
total_revenue = 0
for i in range(len(histogram.bin_counts)):
    income = histogram.bin_centers[i]
    people = histogram.bin_counts[i]
    # Handle top percentile separately
    max_known_income = histogram.source_data.incomes[-1]
    if income > max_known_income:
        income = 202000
    total_revenue += original_calc.calculate_total_deductions(income)[0] * people

# Optimize reformed system
optimal_rate, achieved_revenue = optimize_additional_rate_for_revenue(
    total_revenue, histogram, top_percentile_income=202000
)

# Create reformed calculator
reformed_calc = UKTaxCalculatorReformed(additional_rate=optimal_rate)

# Calculate winners and losers
winners = 0
losers = 0
unchanged = 0
total_winner_savings = 0
total_loser_costs = 0

for i in range(len(histogram.bin_counts)):
    income = histogram.bin_centers[i]
    people = histogram.bin_counts[i]
    
    max_known_income = histogram.source_data.incomes[-1]
    if income > max_known_income:
        income = 202000
    
    original_tax = original_calc.calculate_total_deductions(income)[0]
    reformed_tax = reformed_calc.calculate_total_deductions(income)[0]
    
    diff = reformed_tax - original_tax
    if diff < -0.01:
        winners += people
        total_winner_savings += abs(diff) * people
    elif diff > 0.01:
        losers += people
        total_loser_costs += diff * people
    else:
        unchanged += people

avg_saving = total_winner_savings / winners if winners > 0 else 0
avg_cost = total_loser_costs / losers if losers > 0 else 0

print("\n" + "="*70)
print("WINNERS AND LOSERS ANALYSIS")
print("="*70)
print(f"\nOptimal additional rate: {optimal_rate*100:.2f}%")
print(f"")
print(f"Winners (pay less):   {int(winners):>8,} people  (avg. saving: £{avg_saving:>8,.0f}/year)")
print(f"Losers (pay more):    {int(losers):>8,} people  (avg. cost:   £{avg_cost:>8,.0f}/year)")
print(f"Unchanged:            {int(unchanged):>8,} people")
print(f"")
print(f"Total population:     {int(winners + losers + unchanged):>8,}")
print(f"")
print(f"Total savings for winners:  £{total_winner_savings:>12,.0f}")
print(f"Total costs for losers:     £{total_loser_costs:>12,.0f}")
print(f"Net benefit to society:     £{total_winner_savings - total_loser_costs:>12,.0f}")
print("="*70 + "\n")
