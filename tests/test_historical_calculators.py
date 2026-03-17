#!/usr/bin/env python3
"""Test all four historical UK tax calculators."""

from uktax import (UKTaxCalculatorPre2010, UKTaxCalculator2010, 
                   UKTaxCalculator2013, UKTaxCalculator2023)

print("\n" + "="*90)
print("UK TAX SYSTEM EVOLUTION: Testing All Four Historical Periods")
print("="*90)

# Create calculators for each period
calculators = [
    ("Pre-2010 (Two-Band Era)", UKTaxCalculatorPre2010()),
    ("2010-2013 (50% Additional Rate)", UKTaxCalculator2010()),
    ("2013-2023 (45% Additional Rate)", UKTaxCalculator2013()),
    ("2023-Present (Alignment Era)", UKTaxCalculator2023()),
]

# Test incomes across the range
test_incomes = [30000, 50000, 80000, 100000, 110000, 120000, 150000, 200000]

print("\n" + "="*90)
print("MARGINAL TAX RATES COMPARISON")
print("="*90)
print(f"\n{'Income':<15}", end="")
for name, _ in calculators:
    print(f"{name:<20}", end="")
print()
print("-"*90)

for income in test_incomes:
    print(f"£{income:>12,}   ", end="")
    for name, calc in calculators:
        marginal = calc.calculate_marginal_rate(income)
        # Highlight if in 60% trap (only exists in periods 2, 3, 4)
        if 100000 < income < 120000 and marginal > 55:
            marker = f"{marginal:5.1f}% 🔴"  # Red flag for trap
        else:
            marker = f"{marginal:5.1f}%   "
        print(f"{marker:<18}", end="")
    print()

print("\n" + "="*90)
print("TOTAL TAX + NI PAID")
print("="*90)
print(f"\n{'Income':<15}", end="")
for name, _ in calculators:
    print(f"{name:<20}", end="")
print()
print("-"*90)

for income in test_incomes:
    print(f"£{income:>12,}   ", end="")
    for name, calc in calculators:
        total_tax, _, _ = calc.calculate_total_deductions(income)
        print(f"£{total_tax:>8,.0f}         ", end="")
    print()

print("\n" + "="*90)
print("KEY DIFFERENCES BY PERIOD")
print("="*90)
print("""
1. PRE-2010 (Two-Band Era):
   - Personal Allowance: £6,475 (no taper)
   - Only 2 tax bands: 20% and 40%
   - NI: 11% standard, 1% higher
   - NO 60% TRAP (no taper mechanism existed)

2. 2010-2013 (50% Additional Rate):
   - Personal Allowance: £6,475 (taper introduced at £100k)
   - 3 tax bands: 20%, 40%, 50%
   - Additional rate starts at £150,000
   - NI: 12% standard, 2% higher (increased in 2011)
   - 60% TRAP APPEARS (taper + higher rate)

3. 2013-2023 (45% Adjustment):
   - Personal Allowance: £12,570 by 2021 (taper at £100k)
   - 3 tax bands: 20%, 40%, 45% (reduced from 50%)
   - Additional rate still at £150,000
   - NI: 12% standard, 2% higher
   - 60% TRAP PERSISTS (taper + higher rate)

4. 2023-PRESENT (Alignment Era):
   - Personal Allowance: £12,570 (taper at £100k, gone by £125,140)
   - 3 tax bands: 20%, 40%, 45%
   - Additional rate ALIGNED to £125,140 (end of taper)
   - NI: 8% standard (cut from 12%), 2% higher
   - 60% TRAP INTENSIFIED (taper + higher rate in same zone)
   - Trap now between £100k-£116,760

KEY OBSERVATION:
The 60% trap was introduced in 2010 with the personal allowance taper.
It has persisted through all subsequent periods, with the 2023 alignment
making it more pronounced by having the additional rate start exactly
where the taper ends.
""")
print("="*90 + "\n")

# Calculate the trap zone for periods with taper
print("="*90)
print("60% TRAP ANALYSIS BY PERIOD")
print("="*90)

for name, calc in calculators:
    if hasattr(calc, 'taper_threshold'):
        print(f"\n{name}:")
        print(f"   Taper starts: £{calc.taper_threshold:,}")
        
        # Find where trap ends (when additional rate starts or marginal drops)
        for income in range(100000, 200000, 1000):
            marginal = calc.calculate_marginal_rate(income)
            if income > 100000 and marginal < 55:
                print(f"   Trap ends: ~£{income:,} (marginal rate drops below 60%)")
                print(f"   Additional rate starts: £{calc.higher_rate_threshold:,}")
                break
    else:
        print(f"\n{name}:")
        print(f"   NO TAPER - No 60% trap exists")

print("\n" + "="*90 + "\n")
