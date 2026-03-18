"""Main CLI for UK Tax calculations and visualizations."""
import argparse
import sys
import os

# Ensure interactive backend for CLI BEFORE any matplotlib.pyplot imports
import matplotlib
if not os.environ.get('MPLBACKEND'):
    current_backend = matplotlib.get_backend()
    if current_backend.lower() == 'agg':
        # Try to switch to an interactive backend BEFORE importing pyplot
        for backend in ['TkAgg', 'Qt5Agg', 'GTK3Agg', 'MacOSX']:
            try:
                matplotlib.use(backend, force=True)
                # Verify it worked by checking the backend
                if matplotlib.get_backend().lower() != 'agg':
                    break
            except:
                continue

# NOW import pyplot - backend is set
import matplotlib.pyplot as plt
import numpy as np

# Import uktax components
from uktax.income_data import IncomeDistributionData, IncomeHistogram, UK_INCOME_2023
from uktax.uk_tax_calculator import UKTaxCalculator2023, UKTaxCalculatorReformed, optimize_additional_rate_for_revenue
# Import visualizations AFTER backend is set
from uktax.visualizations import IncomeDistributionVisualizer, TaxVisualization


def create_distribution_and_histogram(population_size=100000, bin_size=1000, max_income=202000):
    """
    Create income distribution and histogram with common parameters.
    
    Args:
        population_size: Size of population to simulate
        bin_size: Size of income bins in pounds
        max_income: Maximum income to consider
        
    Returns:
        Tuple of (IncomeDistributionData, IncomeHistogram)
    """
    distribution = IncomeDistributionData.from_list(
        UK_INCOME_2023, 
        start_percentile=1, 
        year="2023"
    )
    
    histogram = IncomeHistogram.from_distribution(
        distribution,
        population_size=population_size,
        bin_size=bin_size,
        max_income=max_income
    )
    
    return distribution, histogram


def calculate_tax_revenue_cmd(args):
    """Calculate total tax revenue from income distribution."""
    distribution, histogram = create_distribution_and_histogram(
        population_size=args.population,
        bin_size=args.bin_size,
        max_income=args.max_income
    )
    
    calculator = UKTaxCalculator2023()
    results = calculate_tax_revenue(histogram, calculator, args.top_percentile_income)
    print_revenue_report(results)


def calculate_tax_revenue(histogram: IncomeHistogram, 
                         calculator,  # UKTaxCalculatorBase or subclass
                         top_percentile_income: float = 202000) -> dict:
    """
    Calculate total tax revenue from income histogram.
    
    Args:
        histogram: Income histogram for population
        calculator: Tax calculator to use
        top_percentile_income: Assumed income for top 1% (beyond data range)
    
    Returns:
        Dictionary with revenue statistics
    """
    total_tax_revenue = 0
    total_income_tax = 0
    total_ni = 0
    
    # Calculate tax for each income bin
    for i in range(len(histogram.bin_counts)):
        income = histogram.bin_centers[i]
        people = histogram.bin_counts[i]
        
        # Handle top percentile separately
        max_known_income = histogram.source_data.incomes[-1]
        if income > max_known_income:
            income = top_percentile_income
        
        deductions, tax, ni = calculator.calculate_total_deductions(income)
        total_tax_revenue += deductions * people
        total_income_tax += tax * people
        total_ni += ni * people
    
    # Calculate average tax per person
    avg_tax_per_person = total_tax_revenue / histogram.population_size
    avg_income_tax = total_income_tax / histogram.population_size
    avg_ni = total_ni / histogram.population_size
    
    # Calculate effective tax rate
    effective_rate = (avg_tax_per_person / histogram.mean_income) * 100 if histogram.mean_income > 0 else 0
    
    return {
        'population': histogram.population_size,
        'mean_income': histogram.mean_income,
        'median_income': histogram.median_income,
        'total_revenue': total_tax_revenue,
        'total_income_tax': total_income_tax,
        'total_ni': total_ni,
        'avg_tax_per_person': avg_tax_per_person,
        'avg_income_tax': avg_income_tax,
        'avg_ni': avg_ni,
        'effective_rate': effective_rate
    }


def print_revenue_report(results: dict):
    """Print formatted tax revenue report."""
    print(f"\n{'='*70}")
    print(f"UK TAX REVENUE CALCULATION")
    print(f"{'='*70}")
    print(f"\nPOPULATION STATISTICS:")
    print(f"  Population:                {results['population']:>20,}")
    print(f"  Mean Income:               £{results['mean_income']:>19,.2f}")
    print(f"  Median Income:             £{results['median_income']:>19,.2f}")
    
    print(f"\nTOTAL TAX REVENUE:")
    print(f"  Total Revenue (Tax + NI):  £{results['total_revenue']:>19,.2f}")
    print(f"  Total Income Tax:          £{results['total_income_tax']:>19,.2f}")
    print(f"  Total National Insurance:  £{results['total_ni']:>19,.2f}")
    
    print(f"\nPER PERSON AVERAGES:")
    print(f"  Average Tax + NI:          £{results['avg_tax_per_person']:>19,.2f}")
    print(f"  Average Income Tax:        £{results['avg_income_tax']:>19,.2f}")
    print(f"  Average NI:                £{results['avg_ni']:>19,.2f}")
    
    print(f"\nEFFECTIVE RATES:")
    print(f"  Effective Tax Rate:        {results['effective_rate']:>19.2f}%")
    print(f"{'='*70}\n")


def plot_cumulative_and_histogram_cmd(args):
    """Visualize UK income distribution with cumulative and histogram plots."""
    distribution, histogram = create_distribution_and_histogram(
        population_size=args.population,
        bin_size=args.bin_size,
        max_income=args.max_income
    )
    
    visualizer = IncomeDistributionVisualizer(figsize=(12, 12))
    fig, axes = visualizer.plot_cumulative_and_histogram(
        distribution,
        histogram,
        show_top_percent=True
    )
    
    # Check if we have an interactive backend
    backend = matplotlib.get_backend().lower()
    if backend == 'agg':
        # Non-interactive backend, save instead
        output_file = 'income_distribution.png'
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"✓ Plot saved to {output_file} (no interactive display available)")
        print(f"  Tip: Install tkinter for interactive plots: sudo apt-get install python3-tk")
    else:
        plt.show()


def plot_tax_analysis_cmd(args):
    """Visualize UK tax rates and marginal rates."""
    calculator = UKTaxCalculator2023()
    visualizer = TaxVisualization(calculator, figsize=(12, 10))
    
    income_range = np.arange(0, args.max_income_range, args.income_step)
    fig, axes = visualizer.plot_tax_analysis(income_range=income_range)
    
    # Check if we have an interactive backend
    backend = matplotlib.get_backend().lower()
    if backend == 'agg':
        # Non-interactive backend, save instead
        output_file = 'tax_analysis.png'
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"✓ Plot saved to {output_file} (no interactive display available)")
        print(f"  Tip: Install tkinter for interactive plots: sudo apt-get install python3-tk")
    else:
        plt.show()


def plot_reform_cmd(args):
    """Compare original and reformed tax systems with different scenarios."""
    scenario_names = {
        'revenue-neutral': 'Revenue-Neutral Reform',
        'fixed-rate': f'Fixed {args.fixed_rate_percent:.1f}% Rate Reform'
    }
    
    print("\n" + "="*70)
    print(f"TAX REFORM ANALYSIS: {scenario_names[args.scenario]}")
    print("="*70)
    
    # Create distribution and histogram
    distribution, histogram = create_distribution_and_histogram(
        population_size=args.population,
        bin_size=args.bin_size,
        max_income=args.max_income
    )
    
    # Calculate revenue with original calculator
    print("\n1. Calculating revenue with ORIGINAL tax system...")
    original_calculator = UKTaxCalculator2023()
    original_results = calculate_tax_revenue(histogram, original_calculator, args.top_percentile_income)
    target_revenue = original_results['total_revenue']
    
    print(f"   Original total revenue: £{target_revenue:,.2f}")
    print(f"   Original additional rate: {original_calculator.additional_rate*100:.1f}%")
    
    # Set up reformed calculator based on scenario
    print(f"\n2. Setting up REFORMED tax system ({args.scenario})...")
    
    if args.scenario == 'revenue-neutral':
        print("   Finding additional rate that matches original revenue...")
        optimal_rate, achieved_revenue = optimize_additional_rate_for_revenue(
            target_revenue, 
            histogram, 
            args.top_percentile_income
        )
        print(f"   Optimal additional rate: {optimal_rate*100:.2f}%")
        print(f"   Achieved revenue: £{achieved_revenue:,.2f}")
        print(f"   Revenue difference: £{abs(achieved_revenue - target_revenue):,.2f}")
        
    elif args.scenario == 'fixed-rate':
        print(f"   Using fixed additional rate: {args.fixed_rate_percent:.1f}%")
        optimal_rate = args.fixed_rate_percent / 100.0
        reformed_calculator = UKTaxCalculatorReformed(additional_rate=optimal_rate)
        reformed_results = calculate_tax_revenue(histogram, reformed_calculator, args.top_percentile_income)
        achieved_revenue = reformed_results['total_revenue']
        revenue_diff = achieved_revenue - target_revenue
        print(f"   Reformed revenue: £{achieved_revenue:,.2f}")
        if revenue_diff > 0:
            print(f"   Revenue GAIN: £{revenue_diff:,.2f} ({revenue_diff/target_revenue*100:.2f}%)")
        else:
            print(f"   Revenue LOSS: £{abs(revenue_diff):,.2f} ({abs(revenue_diff)/target_revenue*100:.2f}%)")
        

    
    # Create reformed calculator with optimal rate
    reformed_calculator = UKTaxCalculatorReformed(additional_rate=optimal_rate)
    reformed_results = calculate_tax_revenue(histogram, reformed_calculator, args.top_percentile_income)
    
    # Calculate winners and losers from histogram
    print("\n3. Analyzing impact on population...")
    winners = 0
    losers = 0
    unchanged = 0
    total_winner_savings = 0
    total_loser_costs = 0
    
    for i in range(len(histogram.bin_counts)):
        income = histogram.bin_centers[i]
        people = histogram.bin_counts[i]
        
        # Handle top percentile
        max_known_income = histogram.source_data.incomes[-1]
        if income > max_known_income:
            income = args.top_percentile_income
        
        # Calculate tax for both systems
        original_tax = original_calculator.calculate_total_deductions(income)[0]
        reformed_tax = reformed_calculator.calculate_total_deductions(income)[0]
        
        # Categorize (with small tolerance for numerical precision)
        diff = reformed_tax - original_tax
        if diff < -0.01:  # Reformed pays less (winner)
            winners += people
            total_winner_savings += abs(diff) * people
        elif diff > 0.01:  # Reformed pays more (loser)
            losers += people
            total_loser_costs += diff * people
        else:  # Essentially the same
            unchanged += people
    
    avg_saving = total_winner_savings / winners if winners > 0 else 0
    avg_cost = total_loser_costs / losers if losers > 0 else 0
    
    print(f"   Winners (pay less): {int(winners):,} people (avg. saving: £{avg_saving:,.0f}/year)")
    print(f"   Losers (pay more): {int(losers):,} people (avg. cost: £{avg_cost:,.0f}/year)")
    print(f"   Unchanged: {int(unchanged):,} people")
    
    # Create comparison plots
    print("\n4. Creating comparison plots...")
    
    income_range = np.arange(0, args.max_income_range, args.income_step)
    
    # Calculate metrics for both calculators
    original_metrics = original_calculator.calculate_for_range(income_range)
    reformed_metrics = reformed_calculator.calculate_for_range(income_range)
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'Tax Reform Comparison: {scenario_names[args.scenario]}', 
                 fontsize=16, fontweight='bold')
    
    # Plot 1: Marginal Tax Rates
    ax1 = axes[0, 0]
    ax1.plot(income_range/1000, original_metrics['marginal_rate'], 
             'r-', linewidth=2, label='Original (with PA taper)')
    ax1.plot(income_range/1000, reformed_metrics['marginal_rate'], 
             'b--', linewidth=2, label=f'Reformed (no taper, {optimal_rate*100:.2f}% add. rate)')
    ax1.set_xlabel('Gross Income (£1000s)', fontsize=12)
    ax1.set_ylabel('Marginal Tax Rate (%)', fontsize=12)
    ax1.set_title('Marginal Tax Rates Comparison', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=10)
    ax1.set_ylim(0, 70)
    
    # Highlight the 60% trap in original
    trap_incomes = income_range[(original_metrics['marginal_rate'] > 55) & 
                                 (income_range > 100000) & 
                                 (income_range < 125140)]
    if len(trap_incomes) > 0:
        ax1.axvspan(trap_incomes[0]/1000, trap_incomes[-1]/1000, 
                   alpha=0.2, color='red', label='60% trap zone')
    
    # Plot 2: Total Deductions (Tax + NI)
    ax2 = axes[0, 1]
    ax2.plot(income_range/1000, original_metrics['total_deductions']/1000, 
             'r-', linewidth=2, label='Original')
    ax2.plot(income_range/1000, reformed_metrics['total_deductions']/1000, 
             'b--', linewidth=2, label='Reformed')
    ax2.set_xlabel('Gross Income (£1000s)', fontsize=12)
    ax2.set_ylabel('Total Deductions (£1000s)', fontsize=12)
    ax2.set_title('Total Tax + NI Deductions', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=10)
    
    # Plot 3: Effective Tax Rates
    ax3 = axes[1, 0]
    ax3.plot(income_range/1000, original_metrics['effective_rate'], 
             'r-', linewidth=2, label='Original')
    ax3.plot(income_range/1000, reformed_metrics['effective_rate'], 
             'b--', linewidth=2, label='Reformed')
    ax3.set_xlabel('Gross Income (£1000s)', fontsize=12)
    ax3.set_ylabel('Effective Tax Rate (%)', fontsize=12)
    ax3.set_title('Effective Tax Rates', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.legend(fontsize=10)
    
    # Plot 4: Difference in Tax Paid
    ax4 = axes[1, 1]
    tax_difference = reformed_metrics['total_deductions'] - original_metrics['total_deductions']
    ax4.plot(income_range/1000, tax_difference, 'g-', linewidth=2)
    ax4.axhline(y=0, color='k', linestyle='-', linewidth=0.5)
    ax4.fill_between(income_range/1000, 0, tax_difference, 
                     where=(tax_difference > 0), alpha=0.3, color='red', 
                     label='Reformed pays MORE')
    ax4.fill_between(income_range/1000, 0, tax_difference, 
                     where=(tax_difference <= 0), alpha=0.3, color='green', 
                     label='Reformed pays LESS')
    ax4.set_xlabel('Gross Income (£1000s)', fontsize=12)
    ax4.set_ylabel('Tax Difference (£)', fontsize=12)
    ax4.set_title('Tax Difference (Reformed - Original)', fontsize=14, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    ax4.legend(fontsize=10)
    
    plt.tight_layout()
    
    # Print summary comparison
    print("\n" + "="*70)
    if args.scenario == 'revenue-neutral':
        print("REVENUE COMPARISON SUMMARY (Revenue Neutral)")
    else:
        print(f"REVENUE COMPARISON SUMMARY (Fixed {args.fixed_rate_percent:.1f}% Rate)")
    print("="*70)
    print(f"\n{'Metric':<40} {'Original':<15} {'Reformed':<15}")
    print("-"*70)
    print(f"{'Additional Rate':<40} {original_calculator.additional_rate*100:>14.1f}% {reformed_calculator.additional_rate*100:>14.2f}%")
    print(f"{'Personal Allowance Taper':<40} {'Yes':>15} {'No':>15}")
    print(f"{'Total Revenue':<40} £{original_results['total_revenue']:>13,.0f} £{reformed_results['total_revenue']:>13,.0f}")
    
    revenue_diff = reformed_results['total_revenue'] - original_results['total_revenue']
    if abs(revenue_diff) < 1:
        print(f"{'Revenue Difference':<40} {'':<15} £{revenue_diff:>13,.0f} (neutral)")
    elif revenue_diff > 0:
        print(f"{'Revenue Difference':<40} {'':<15} £{revenue_diff:>13,.0f} (GAIN)")
    else:
        print(f"{'Revenue Difference':<40} {'':<15} £{revenue_diff:>13,.0f} (LOSS)")
    
    print(f"{'Revenue Match (%)':<40} {'100.0%':>15} {(reformed_results['total_revenue']/original_results['total_revenue']*100):>14.3f}%")
    print(f"{'Avg Tax Per Person':<40} £{original_results['avg_tax_per_person']:>13,.0f} £{reformed_results['avg_tax_per_person']:>13,.0f}")
    print(f"{'Effective Rate':<40} {original_results['effective_rate']:>14.2f}% {reformed_results['effective_rate']:>14.2f}%")
    print("="*70 + "\n")
    
    # Check if we have an interactive backend
    backend = matplotlib.get_backend().lower()
    if backend == 'agg':
        # Non-interactive backend, save instead
        output_file = 'tax_reform_comparison.png'
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"✓ Plot saved to {output_file} (no interactive display available)")
        print(f"  Tip: Install tkinter for interactive plots: sudo apt-get install python3-tk\n")
    else:
        plt.show()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='UK Tax Calculations and Visualizations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s revenue
  %(prog)s revenue --population 1000000
  %(prog)s plot-income
  %(prog)s plot-tax --max-income-range 200000
  %(prog)s plot-reform
  %(prog)s plot-reform --population 500000
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    subparsers.required = True
    
    # Revenue calculation command
    revenue_parser = subparsers.add_parser(
        'revenue',
        help='Calculate total tax revenue from income distribution'
    )
    revenue_parser.add_argument(
        '--population',
        type=int,
        default=100000,
        help='Population size to simulate (default: 100000)'
    )
    revenue_parser.add_argument(
        '--bin-size',
        type=int,
        default=1000,
        help='Income bin size in pounds (default: 1000)'
    )
    revenue_parser.add_argument(
        '--max-income',
        type=int,
        default=202000,
        help='Maximum income to consider (default: 202000)'
    )
    revenue_parser.add_argument(
        '--top-percentile-income',
        type=float,
        default=202000,
        help='Assumed income for top 1%% (default: 202000)'
    )
    revenue_parser.set_defaults(func=calculate_tax_revenue_cmd)
    
    # Income distribution plot command
    plot_income_parser = subparsers.add_parser(
        'plot-income',
        help='Plot cumulative and histogram of income distribution'
    )
    plot_income_parser.add_argument(
        '--population',
        type=int,
        default=100000,
        help='Population size to simulate (default: 100000)'
    )
    plot_income_parser.add_argument(
        '--bin-size',
        type=int,
        default=1000,
        help='Income bin size in pounds (default: 1000)'
    )
    plot_income_parser.add_argument(
        '--max-income',
        type=int,
        default=202000,
        help='Maximum income to consider (default: 202000)'
    )
    plot_income_parser.set_defaults(func=plot_cumulative_and_histogram_cmd)
    
    # Tax analysis plot command
    plot_tax_parser = subparsers.add_parser(
        'plot-tax',
        help='Plot tax rates and marginal rates analysis'
    )
    plot_tax_parser.add_argument(
        '--max-income-range',
        type=int,
        default=160000,
        help='Maximum income for tax analysis (default: 160000)'
    )
    plot_tax_parser.add_argument(
        '--income-step',
        type=int,
        default=1000,
        help='Income increment step (default: 1000)'
    )
    plot_tax_parser.set_defaults(func=plot_tax_analysis_cmd)
    
    # Tax reform comparison plot command
    plot_reform_parser = subparsers.add_parser(
        'plot-reform',
        help='Compare original vs reformed tax system with different scenarios'
    )
    plot_reform_parser.add_argument(
        '--scenario',
        type=str,
        choices=['revenue-neutral', 'fixed-rate'],
        default='revenue-neutral',
        help='Reform scenario: revenue-neutral (optimize for same revenue) or fixed-rate (use specified rate)'
    )
    plot_reform_parser.add_argument(
        '--fixed-rate-percent',
        type=float,
        default=45.0,
        help='Additional rate percentage for fixed-rate scenario (default: 45.0)'
    )
    plot_reform_parser.add_argument(
        '--population',
        type=int,
        default=100000,
        help='Population size to simulate (default: 100000)'
    )
    plot_reform_parser.add_argument(
        '--bin-size',
        type=int,
        default=1000,
        help='Income bin size in pounds (default: 1000)'
    )
    plot_reform_parser.add_argument(
        '--max-income',
        type=int,
        default=202000,
        help='Maximum income to consider (default: 202000)'
    )
    plot_reform_parser.add_argument(
        '--top-percentile-income',
        type=float,
        default=202000,
        help='Assumed income for top 1%% (default: 202000)'
    )
    plot_reform_parser.add_argument(
        '--max-income-range',
        type=int,
        default=160000,
        help='Maximum income for visualization (default: 160000)'
    )
    plot_reform_parser.add_argument(
        '--income-step',
        type=int,
        default=1000,
        help='Income increment step (default: 1000)'
    )
    plot_reform_parser.set_defaults(func=plot_reform_cmd)
    
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
