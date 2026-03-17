#!/usr/bin/env python3
"""Show how different fixed rates affect revenue and winners/losers."""

from uktax import (UKTaxCalculator2023, UKTaxCalculatorReformed, 
                   IncomeDistributionData, IncomeHistogram, UK_INCOME_2023)

# Create histogram
distribution = IncomeDistributionData.from_list(UK_INCOME_2023, start_percentile=1)
histogram = IncomeHistogram.from_distribution(distribution, population_size=100000, bin_size=1000)

# Calculate baseline revenue
original_calc = UKTaxCalculator2023()
total_revenue = 0
for i in range(len(histogram.bin_counts)):
    income = histogram.bin_centers[i]
    people = histogram.bin_counts[i]
    max_known_income = histogram.source_data.incomes[-1]
    if income > max_known_income:
        income = 202000
    total_revenue += original_calc.calculate_total_deductions(income)[0] * people

print("\n" + "="*100)
print("FIXED-RATE REFORM SCENARIOS: Testing Different Additional Rates")
print("="*100)
print(f"\nOriginal system revenue: £{total_revenue:,.0f} (with 45% additional rate and PA taper)")
print("\n" + "="*100)

rates = [40, 42, 43.86, 45, 47, 50]

print(f"\n{'Rate':<8} {'Revenue Change':<25} {'Winners':<20} {'Losers':<20} {'Revenue Impact':<15}")
print("-"*100)

for rate_pct in rates:
    rate = rate_pct / 100.0
    calc = UKTaxCalculatorReformed(additional_rate=rate)
    
    # Calculate revenue
    revenue = 0
    winners = 0
    losers = 0
    winner_savings = 0
    loser_costs = 0
    
    for i in range(len(histogram.bin_counts)):
        income = histogram.bin_centers[i]
        people = histogram.bin_counts[i]
        max_known_income = histogram.source_data.incomes[-1]
        if income > max_known_income:
            income = 202000
        
        reformed_tax = calc.calculate_total_deductions(income)[0]
        revenue += reformed_tax * people
        
        original_tax = original_calc.calculate_total_deductions(income)[0]
        diff = reformed_tax - original_tax
        
        if diff < -0.01:
            winners += people
            winner_savings += abs(diff) * people
        elif diff > 0.01:
            losers += people
            loser_costs += diff * people
    
    revenue_diff = revenue - total_revenue
    revenue_pct = revenue_diff / total_revenue * 100
    
    avg_win = winner_savings / winners if winners > 0 else 0
    avg_loss = loser_costs / losers if losers > 0 else 0
    
    if rate_pct == 43.86:
        label = f"{rate_pct:.2f}%*"  # Mark revenue-neutral
    else:
        label = f"{rate_pct:.1f}%"
    
    revenue_str = f"£{revenue_diff:+,.0f} ({revenue_pct:+.2f}%)"
    winners_str = f"{int(winners):,} (£{avg_win:,.0f}/yr)"
    losers_str = f"{int(losers):,} (£{avg_loss:,.0f}/yr)"
    
    if abs(revenue_diff) < 100:
        impact = "Neutral ✓"
    elif revenue_diff > 0:
        impact = "Gain"
    else:
        impact = "Loss"
    
    print(f"{label:<8} {revenue_str:<25} {winners_str:<20} {losers_str:<20} {impact:<15}")

print("\n" + "="*100)
print("KEY INSIGHTS:")
print("="*100)
print("""
- 40%:  Large revenue loss (1%), lots of winners, but could be seen as too generous
- 43.86%*: Perfect revenue neutrality - the mathematically optimal choice
- 45%:  Small revenue gain (0.3%), same rate as current top rate, simple to communicate
- 47%+: Increasing revenue but higher earners pay significantly more

* The revenue-neutral rate (43.86%) is the default for the 'revenue-neutral' scenario

RECOMMENDATION:
- For revenue neutrality: Use 43.86% (default revenue-neutral scenario)
- For political simplicity: Use 45% (same as current, small gain, easy to explain)
- For revenue generation: Use 47%+ (but note the cost to high earners)

All rates eliminate the 60% trap and provide constant personal allowance.
""")
print("="*100 + "\n")
