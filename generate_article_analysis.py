#!/usr/bin/env python3
"""Generate all analysis, plots, and data for the comprehensive article."""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from uktax import (
    UK_INCOME_BY_YEAR,
    IncomeDistributionData,
    IncomeHistogram,
    UKTaxCalculatorPre2010,
    UKTaxCalculator2010,
    UKTaxCalculator2013,
    UKTaxCalculator2023,
    UKTaxCalculatorReformed,
    optimize_additional_rate_for_revenue
)

# Create output directory
OUTPUT_DIR = Path("article_assets")
OUTPUT_DIR.mkdir(exist_ok=True)

POPULATION = 100000

def plot_income_distribution(year_key, title, filename):
    """Plot income distribution for a specific year."""
    income_data = IncomeDistributionData.from_list(
        UK_INCOME_BY_YEAR[year_key],
        start_percentile=1,
        year=year_key
    )
    
    # Create histogram for population distribution
    histogram = IncomeHistogram.from_distribution(
        income_data,
        population_size=POPULATION,
        bin_size=1000,
        max_income=210000
    )
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Top plot: Income vs Percentile
    percentiles = income_data.percentiles
    incomes = income_data.incomes / 1000  # Convert to thousands
    
    ax1.plot(percentiles, incomes, linewidth=2, color='#2E86AB')
    ax1.fill_between(percentiles, 0, incomes, alpha=0.3, color='#2E86AB')
    
    ax1.set_xlabel('Percentile', fontsize=12)
    ax1.set_ylabel('Income (£thousands)', fontsize=12)
    ax1.set_title(title, fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # Add key percentile markers with percentile labels
    for p in [10, 25, 50, 75, 90, 99]:
        income = income_data.get_income_at_percentile(p)
        ax1.plot(p, income/1000, 'ro', markersize=6)
        # Annotate with both percentile and income
        ax1.annotate(f'p{p}\n£{income/1000:.0f}k',
                   xy=(p, income/1000),
                   xytext=(5, 5),
                   textcoords='offset points',
                   fontsize=9,
                   ha='left')
    
    # Bottom plot: Histogram of population by income bin
    income_bins_k = histogram.bin_centers / 1000  # Convert to thousands
    
    # Find the 99th percentile income to identify top 1%
    p99_income = income_data.get_income_at_percentile(99)
    
    # Color bars: pink for bins above 99th percentile (top 1%), blue otherwise
    # Only color bins that have non-zero population
    colors = []
    top_1_percent_bins = []
    for i in range(len(histogram.bin_counts)):
        if histogram.bin_counts[i] > 0:  # Only consider non-empty bins
            if histogram.bin_centers[i] > p99_income:
                colors.append('#FF69B4')  # Pink for top 1%
                top_1_percent_bins.append(i)
            else:
                colors.append('#2E86AB')  # Blue
        else:
            colors.append('#2E86AB')  # Blue for empty bins (won't show anyway)
    
    ax2.bar(income_bins_k, histogram.bin_counts, width=0.9, color=colors, alpha=0.7, edgecolor='black')
    
    # Add annotation for top 1% bins if they exist
    if top_1_percent_bins:
        # Use the first bin of the top 1% for annotation
        top_bin_idx = top_1_percent_bins[0]
        top_bin_income = income_bins_k[top_bin_idx]
        # Sum up all people in top 1% bins
        top_1_percent_count = sum(histogram.bin_counts[i] for i in top_1_percent_bins)
        ax2.annotate(f'Top 1%\n({int(top_1_percent_count):,} people)',
                    xy=(top_bin_income, histogram.bin_counts[top_bin_idx]),
                    xytext=(10, 10),
                    textcoords='offset points',
                    fontsize=9,
                    color='#FF69B4',
                    fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#FF69B4', alpha=0.8))
    
    # Add mean income line
    mean_income_k = histogram.mean_income / 1000
    ax2.axvline(x=mean_income_k, color='green', linestyle='--', linewidth=2, 
                label=f'Mean: £{mean_income_k:.1f}k', alpha=0.7)
    
    ax2.set_xlabel('Income (£thousands)', fontsize=12)
    ax2.set_ylabel('Number of People (per £1k bin)', fontsize=12)
    ax2.set_title(f'Population Distribution by Income ({year_key})', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)  # Grid on both axes
    ax2.legend(fontsize=10, loc='upper right')
    ax2.set_xlim([0, 210])
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Generated {filename}")
    
    return income_data


def calculate_tax_revenue(calculator, year_key, calculator_name):
    """Calculate total tax revenue for a given calculator and year."""
    income_data = IncomeDistributionData.from_list(
        UK_INCOME_BY_YEAR[year_key],
        start_percentile=1,
        year=year_key
    )
    
    histogram = IncomeHistogram.from_distribution(
        income_data,
        population_size=POPULATION,
        bin_size=1000,
        max_income=210000
    )
    
    total_revenue = 0
    total_income_tax = 0
    total_ni = 0
    
    max_known_income = income_data.incomes[-1]
    top_percentile_income = max_known_income * 1.15  # Estimate for top 1%
    
    for i in range(len(histogram.bin_counts)):
        income = histogram.bin_centers[i]
        people = histogram.bin_counts[i]
        
        if income > max_known_income:
            income = top_percentile_income
        
        total_ded, income_tax, ni = calculator.calculate_total_deductions(income)
        total_revenue += total_ded * people
        total_income_tax += income_tax * people
        total_ni += ni * people
    
    print(f"\n{calculator_name} using {year_key} income distribution:")
    print(f"  Total Revenue: £{total_revenue:,.0f}")
    print(f"  Income Tax: £{total_income_tax:,.0f}")
    print(f"  National Insurance: £{total_ni:,.0f}")
    print(f"  Mean Income: £{histogram.mean_income:,.0f}")
    
    return total_revenue, histogram


def plot_marginal_rates(calculator, label, color, ax=None):
    """Plot marginal tax rates for a calculator."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 6))
    
    incomes = np.linspace(0, 200000, 2000)
    marginal_rates = [calculator.calculate_marginal_rate(i) for i in incomes]
    
    ax.plot(incomes/1000, marginal_rates, label=label, linewidth=2, color=color)
    
    return ax


def plot_tax_difference(calc1, calc2, name1, name2, filename, year_key):
    """Plot the difference in total tax between two calculators."""
    incomes = np.linspace(0, 200000, 2000)
    
    # Calculate marginal rates, effective rates, and tax difference
    marginal_rates_1 = [calc1.calculate_marginal_rate(i) for i in incomes]
    marginal_rates_2 = [calc2.calculate_marginal_rate(i) for i in incomes]
    
    effective_rates_1 = [calc1.calculate_effective_rate(i) for i in incomes]
    effective_rates_2 = [calc2.calculate_effective_rate(i) for i in incomes]
    
    diff = []
    for income in incomes:
        tax1 = calc1.calculate_total_deductions(income)[0]
        tax2 = calc2.calculate_total_deductions(income)[0]
        diff.append(tax2 - tax1)
    
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 14))
    
    # Plot 1: Marginal rates comparison
    ax1.plot(incomes/1000, marginal_rates_1, label=name1, linewidth=2, color='#D32F2F')
    ax1.plot(incomes/1000, marginal_rates_2, label=name2, linewidth=2, color='#1976D2')
    
    ax1.set_xlabel('Income (£thousands)', fontsize=12)
    ax1.set_ylabel('Marginal Tax Rate (%)', fontsize=12)
    ax1.set_title(f'Marginal Tax Rates: {name1} vs {name2}', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim([0, 70])
    
    # Highlight 60% trap region if present
    for calc, name in [(calc1, name1), (calc2, name2)]:
        if hasattr(calc, 'taper_threshold'):
            ax1.axvspan(calc.taper_threshold/1000, 
                       (calc.taper_threshold + calc.personal_allowance*2)/1000,
                       alpha=0.1, color='red')
    
    # Plot 2: Effective rates comparison
    ax2.plot(incomes/1000, effective_rates_1, label=name1, linewidth=2, color='#D32F2F')
    ax2.plot(incomes/1000, effective_rates_2, label=name2, linewidth=2, color='#1976D2')
    
    ax2.set_xlabel('Income (£thousands)', fontsize=12)
    ax2.set_ylabel('Effective Tax Rate (%)', fontsize=12)
    ax2.set_title(f'Effective Tax Rates: {name1} vs {name2}', fontsize=12, fontweight='bold')
    ax2.legend(fontsize=11)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim([0, 50])
    
    # Plot 3: Tax difference
    ax3.plot(incomes/1000, diff, linewidth=2, color='#7B1FA2')
    ax3.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    ax3.fill_between(incomes/1000, 0, diff, 
                     where=np.array(diff) > 0, alpha=0.3, color='red', label='Pay more')
    ax3.fill_between(incomes/1000, 0, diff,
                     where=np.array(diff) < 0, alpha=0.3, color='green', label='Pay less')
    
    ax3.set_xlabel('Income (£thousands)', fontsize=12)
    ax3.set_ylabel('Tax Difference (£)', fontsize=12)
    ax3.set_title(f'Annual Tax Difference: {name2} minus {name1}', fontsize=12, fontweight='bold')
    ax3.legend(fontsize=11)
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Generated {filename}")


def calculate_winners_losers(calc1, calc2, name1, name2, year_key):
    """Calculate winners and losers between two tax systems."""
    income_data = IncomeDistributionData.from_list(
        UK_INCOME_BY_YEAR[year_key],
        start_percentile=1,
        year=year_key
    )
    
    histogram = IncomeHistogram.from_distribution(
        income_data,
        population_size=POPULATION,
        bin_size=1000,
        max_income=210000
    )
    
    winners_count = 0
    losers_count = 0
    unchanged_count = 0
    
    winners_savings = 0
    losers_costs = 0
    
    max_known_income = income_data.incomes[-1]
    top_percentile_income = max_known_income * 1.15
    
    for i in range(len(histogram.bin_counts)):
        income = histogram.bin_centers[i]
        people = histogram.bin_counts[i]
        
        if income > max_known_income:
            income = top_percentile_income
        
        tax1 = calc1.calculate_total_deductions(income)[0]
        tax2 = calc2.calculate_total_deductions(income)[0]
        diff = tax2 - tax1
        
        if abs(diff) < 1:  # Less than £1 difference
            unchanged_count += people
        elif diff < 0:  # Pay less under new system
            winners_count += people
            winners_savings += abs(diff) * people
        else:  # Pay more under new system
            losers_count += people
            losers_costs += diff * people
    
    print(f"\nWinners/Losers: {name1} → {name2}")
    print(f"  Winners (pay less): {int(winners_count):,} ({winners_count/POPULATION*100:.1f}%)")
    if winners_count > 0:
        print(f"    Average saving: £{winners_savings/winners_count:,.0f}/year")
        print(f"    Total savings: £{winners_savings:,.0f}")
    
    print(f"  Losers (pay more): {int(losers_count):,} ({losers_count/POPULATION*100:.1f}%)")
    if losers_count > 0:
        print(f"    Average cost: £{losers_costs/losers_count:,.0f}/year")
        print(f"    Total costs: £{losers_costs:,.0f}")
    
    print(f"  Unchanged: {int(unchanged_count):,} ({unchanged_count/POPULATION*100:.1f}%)")
    print(f"  Net revenue change: £{losers_costs - winners_savings:,.0f}")
    
    return {
        'winners_count': int(winners_count),
        'winners_pct': winners_count/POPULATION*100,
        'winners_avg_saving': winners_savings/winners_count if winners_count > 0 else 0,
        'winners_total': winners_savings,
        'losers_count': int(losers_count),
        'losers_pct': losers_count/POPULATION*100,
        'losers_avg_cost': losers_costs/losers_count if losers_count > 0 else 0,
        'losers_total': losers_costs,
        'unchanged_count': int(unchanged_count),
        'unchanged_pct': unchanged_count/POPULATION*100,
        'net_revenue_change': losers_costs - winners_savings
    }


def plot_current_trap():
    """Plot the current 60% trap with both marginal and effective rates."""
    calc = UKTaxCalculator2023()
    
    incomes = np.linspace(0, 200000, 2000)
    marginal_rates = [calc.calculate_marginal_rate(i) for i in incomes]
    effective_rates = [calc.calculate_effective_rate(i) for i in incomes]
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Top plot: Marginal tax rate
    ax1.plot(incomes/1000, marginal_rates, linewidth=3, color='#D32F2F', label='Marginal Rate')
    
    # Vertical red bar over trap region instead of horizontal
    ax1.axvspan(100, 125.14, alpha=0.2, color='red', label='60% Trap Zone')
    
    ax1.axvline(x=100, color='black', linestyle='--', alpha=0.5, linewidth=1.5)
    ax1.axvline(x=125.14, color='black', linestyle=':', alpha=0.5, linewidth=1.5)
    
    # Annotate the trap
    ax1.annotate('60% Marginal Rate Trap',
                xy=(112.5, 62), xytext=(130, 67),
                fontsize=12, fontweight='bold', color='darkred',
                arrowprops=dict(arrowstyle='->', color='darkred', lw=2))
    
    ax1.text(100, 2, 'Taper starts\n£100k', ha='center', va='bottom', fontsize=9, alpha=0.7)
    ax1.text(125.14, 2, 'Additional\nrate\n£125.14k', ha='center', va='bottom', fontsize=9, alpha=0.7)
    
    ax1.set_xlabel('Income (£thousands)', fontsize=12)
    ax1.set_ylabel('Marginal Tax Rate (%)', fontsize=12)
    ax1.set_title('The 60% Marginal Rate Trap (2023-Present)', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=10, loc='upper right')
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim([0, 70])
    ax1.set_xlim([0, 200])
    
    # Bottom plot: Effective tax rate
    ax2.plot(incomes/1000, effective_rates, linewidth=3, color='#1976D2', label='Effective Rate')
    ax2.axvline(x=100, color='black', linestyle='--', alpha=0.5, label='Taper starts (£100k)')
    ax2.axvline(x=125.14, color='black', linestyle=':', alpha=0.5, label='Additional rate (£125.14k)')
    
    ax2.set_xlabel('Income (£thousands)', fontsize=12)
    ax2.set_ylabel('Effective Tax Rate (%)', fontsize=12)
    ax2.set_title('Effective Tax Rate (Total Tax ÷ Gross Income)', fontsize=12, fontweight='bold')
    ax2.legend(fontsize=10, loc='lower right')
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim([0, 50])
    ax2.set_xlim([0, 200])
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'current_trap.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Generated current_trap.png")


def main():
    """Generate all analysis and plots."""
    print("="*70)
    print("GENERATING ARTICLE ANALYSIS AND PLOTS")
    print("="*70)
    
    # Current trap visualization
    print("\n[1] Current 60% Trap")
    plot_current_trap()
    
    # Historical period 1: Pre-2010
    print("\n[2] Period 1: Pre-2010 (Two-Band Era)")
    plot_income_distribution("2009/10", 
                            "UK Income Distribution 2009/10\n(Pre-Additional Rate Era)",
                            "income_dist_2009_10.png")
    calc_pre2010 = UKTaxCalculatorPre2010()
    revenue_pre2010, hist_pre2010 = calculate_tax_revenue(calc_pre2010, "2009/10", "Pre-2010 System")
    
    # Historical period 2: 2010-2013
    print("\n[3] Period 2: 2010-2013 (50% Additional Rate)")
    calc_2010 = UKTaxCalculator2010()
    revenue_2010, hist_2010 = calculate_tax_revenue(calc_2010, "2010/11", "2010-2013 System")
    
    plot_tax_difference(calc_pre2010, calc_2010,
                       "Pre-2010", "2010-2013",
                       "comparison_pre2010_vs_2010.png",
                       "2010/11")
    
    wl_2010 = calculate_winners_losers(calc_pre2010, calc_2010,
                                       "Pre-2010", "2010-2013",
                                       "2010/11")
    
    # Historical period 3: 2013-2023
    print("\n[4] Period 3: 2013-2023 (45% Adjustment Era)")
    plot_income_distribution("2012/13",
                            "UK Income Distribution 2012/13\n(Mid 45% Era)",
                            "income_dist_2012_13.png")
    calc_2013 = UKTaxCalculator2013()
    revenue_2013, hist_2013 = calculate_tax_revenue(calc_2013, "2013/14", "2013-2023 System")
    
    plot_tax_difference(calc_2010, calc_2013,
                       "2010-2013", "2013-2023",
                       "comparison_2010_vs_2013.png",
                       "2013/14")
    
    wl_2013 = calculate_winners_losers(calc_2010, calc_2013,
                                       "2010-2013", "2013-2023",
                                       "2013/14")
    
    # Historical period 4: 2023-Present
    print("\n[5] Period 4: 2023-Present (Alignment Era)")
    plot_income_distribution("2022/23",
                            "UK Income Distribution 2022/23\n(Current Era)",
                            "income_dist_2022_23.png")
    calc_2023 = UKTaxCalculator2023()
    revenue_2023, hist_2023 = calculate_tax_revenue(calc_2023, "2022/23", "2023-Present System")
    
    plot_tax_difference(calc_2013, calc_2023,
                       "2013-2023", "2023-Present",
                       "comparison_2013_vs_2023.png",
                       "2022/23")
    
    wl_2023 = calculate_winners_losers(calc_2013, calc_2023,
                                       "2013-2023", "2023-Present",
                                       "2022/23")
    
    # Reform 1: Revenue-neutral
    print("\n[6] Reform 1: Revenue-Neutral (Optimized Additional Rate)")
    
    # Calculate top percentile income the same way as revenue calculation
    max_known_income = hist_2023.source_data.incomes[-1]
    top_percentile_income = max_known_income * 1.15
    
    optimal_rate, achieved_revenue = optimize_additional_rate_for_revenue(
        revenue_2023, hist_2023, top_percentile_income=top_percentile_income
    )
    print(f"  Optimal additional rate: {optimal_rate*100:.2f}%")
    print(f"  Target revenue: £{revenue_2023:,.0f}")
    print(f"  Achieved revenue: £{achieved_revenue:,.0f}")
    print(f"  Difference: £{abs(achieved_revenue - revenue_2023):,.0f}")
    
    calc_reformed_neutral = UKTaxCalculatorReformed(additional_rate=optimal_rate)
    
    plot_tax_difference(calc_2023, calc_reformed_neutral,
                       "Current (2023)", "Reformed (Revenue-Neutral)",
                       "comparison_2023_vs_reformed_neutral.png",
                       "2022/23")
    
    wl_reformed_neutral = calculate_winners_losers(calc_2023, calc_reformed_neutral,
                                                    "Current (2023)", "Reformed (Revenue-Neutral)",
                                                    "2022/23")
    
    # Reform 2: Fixed 45% rate
    print("\n[7] Reform 2: Fixed 45% Additional Rate")
    calc_reformed_45 = UKTaxCalculatorReformed(additional_rate=0.45)
    revenue_reformed_45, _ = calculate_tax_revenue(calc_reformed_45, "2022/23", "Reformed (45%) System")
    
    plot_tax_difference(calc_2023, calc_reformed_45,
                       "Current (2023)", "Reformed (45%)",
                       "comparison_2023_vs_reformed_45.png",
                       "2022/23")
    
    wl_reformed_45 = calculate_winners_losers(calc_2023, calc_reformed_45,
                                               "Current (2023)", "Reformed (45%)",
                                               "2022/23")
    
    print("\n" + "="*70)
    print("ALL ANALYSIS COMPLETE!")
    print(f"Output directory: {OUTPUT_DIR.absolute()}")
    print("="*70)
    
    # Return summary data for article generation
    return {
        'revenue_pre2010': revenue_pre2010,
        'revenue_2010': revenue_2010,
        'revenue_2013': revenue_2013,
        'revenue_2023': revenue_2023,
        'revenue_reformed_neutral': achieved_revenue,
        'revenue_reformed_45': revenue_reformed_45,
        'optimal_rate': optimal_rate,
        'wl_2010': wl_2010,
        'wl_2013': wl_2013,
        'wl_2023': wl_2023,
        'wl_reformed_neutral': wl_reformed_neutral,
        'wl_reformed_45': wl_reformed_45,
    }


if __name__ == "__main__":
    data = main()
