"""Visualization classes for income distribution and tax analysis."""
import matplotlib.pyplot as plt
import numpy as np
from typing import Optional, List, Tuple
from uktax.income_data import IncomeDistributionData, IncomeHistogram
from uktax.uk_tax_calculator import UKTaxCalculatorBase


class IncomeDistributionVisualizer:
    """Visualizes income distribution data."""
    
    def __init__(self, figsize: Tuple[int, int] = (12, 12)):
        self.figsize = figsize
    
    def plot_cumulative_and_histogram(self, 
                                     distribution: IncomeDistributionData,
                                     histogram: IncomeHistogram,
                                     show_top_percent: bool = True,
                                     key_percentiles: Optional[List[int]] = None):
        """
        Plot cumulative distribution and population histogram.
        
        Args:
            distribution: Raw income distribution data
            histogram: Calculated histogram data
            show_top_percent: Whether to show special bar for top percentile
            key_percentiles: List of percentiles to annotate (default: [25, 50, 75, 90, 95, 99])
        """
        if key_percentiles is None:
            key_percentiles = [25, 50, 75, 90, 95, 99]
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=self.figsize)
        
        # Top subplot: Cumulative distribution
        self._plot_cumulative(ax1, distribution, key_percentiles)
        
        # Bottom subplot: Histogram
        self._plot_histogram(ax2, histogram, show_top_percent)
        
        plt.tight_layout()
        return fig, (ax1, ax2)
    
    def _plot_cumulative(self, ax, distribution: IncomeDistributionData, 
                        key_percentiles: List[int]):
        """Plot cumulative income distribution."""
        ax.plot(distribution.percentiles, distribution.incomes, 
               color='blue', linewidth=2, marker='o', markersize=3)
        ax.set_title(f'UK Taxable Income Distribution {distribution.year} (Cumulative)', 
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('Percentile')
        ax.set_ylabel('Taxable Income (£)')
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, 100)
        
        # Add reference lines for key percentiles
        for percentile in key_percentiles:
            if percentile <= len(distribution.percentiles):
                income = distribution.get_income_at_percentile(percentile)
                ax.axvline(x=percentile, color='red', linestyle='--', alpha=0.3)
                ax.axhline(y=income, color='red', linestyle='--', alpha=0.3)
                ax.annotate(f'P{percentile}: £{income:,.0f}', 
                           xy=(percentile, income), 
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=9, bbox=dict(boxstyle='round,pad=0.3', 
                                                facecolor='yellow', alpha=0.7))
    
    def _plot_histogram(self, ax, histogram: IncomeHistogram, show_top_percent: bool):
        """Plot population histogram."""
        bin_centers = histogram.bin_centers
        bin_counts = histogram.bin_counts
        
        # Determine if we need to handle top percentile separately
        max_known_income = histogram.source_data.incomes[-1]
        
        # Plot regular bins (all data within known range)
        regular_bins_mask = bin_centers <= max_known_income
        ax.bar(bin_centers[regular_bins_mask], bin_counts[regular_bins_mask], 
              width=histogram.income_bins[1] - histogram.income_bins[0] - 100,
              color='green', alpha=0.7, edgecolor='black', linewidth=0.3, 
              label='Data')
        
        # Plot special bin for top percentile if requested
        if show_top_percent:
            top_income, top_count = histogram.get_top_percentile_bin(99)
            ax.bar(top_income, top_count, width=7000, 
                  color='red', alpha=0.5, edgecolor='black', linewidth=0.5, 
                  label=f'£{max_known_income/1000:.0f}k+ (Top 1%)')
        
        # Add vertical line for mean income
        ax.axvline(x=histogram.mean_income, color='purple', 
                  linestyle='--', linewidth=2, 
                  label=f'Mean: £{histogram.mean_income:,.0f}')
        
        ax.set_title(f'Population Distribution by Income (Population: {histogram.population_size:,})', 
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('Income (£)')
        ax.set_ylabel('Number of People')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Format x-axis
        max_x = int(max_known_income * 1.1)
        tick_positions = np.arange(0, max_x, 10000)
        ax.set_xticks(tick_positions)
        ax.set_xticklabels([f'{int(x/1000)}k' for x in tick_positions], rotation=45)
        ax.set_xlim(0, max_x)
        
        # Annotate the tallest bar
        max_bin_idx = np.argmax(bin_counts[regular_bins_mask])
        max_bin_count = bin_counts[max_bin_idx]
        max_bin_income = bin_centers[max_bin_idx]
        bin_width = histogram.income_bins[1] - histogram.income_bins[0]
        ax.annotate(f'{max_bin_count:,.0f} people\n£{histogram.income_bins[max_bin_idx]/1000:.0f}k-£{histogram.income_bins[max_bin_idx+1]/1000:.0f}k', 
                   xy=(max_bin_income, max_bin_count), 
                   xytext=(10, 10), textcoords='offset points',
                   fontsize=9, color='darkgreen', fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))


class TaxVisualization:
    """Visualizes tax calculations and marginal rates."""
    
    def __init__(self, tax_calculator: UKTaxCalculatorBase, figsize: Tuple[int, int] = (12, 10)):
        self.calculator = tax_calculator
        self.figsize = figsize
    
    def plot_tax_analysis(self, 
                         income_range: Optional[np.ndarray] = None,
                         max_income: int = 160000,
                         step: int = 1000):
        """
        Plot comprehensive tax analysis including deductions and marginal rates.
        
        Args:
            income_range: Array of incomes to analyze (if None, creates default range)
            max_income: Maximum income for default range
            step: Step size for default range
        """
        if income_range is None:
            income_range = np.arange(0, max_income, step)
        
        results = self.calculator.calculate_for_range(income_range)
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=self.figsize)
        
        # Top subplot: Income and deductions
        self._plot_income_deductions(ax1, results)
        
        # Bottom subplot: Marginal tax rate
        self._plot_marginal_rates(ax2, results)
        
        plt.tight_layout()
        return fig, (ax1, ax2)
    
    def _plot_income_deductions(self, ax, results: dict):
        """Plot gross income, net income, and deductions."""
        incomes = results['gross_income']
        net = results['net_income']
        
        ax.plot(incomes, incomes, label='Gross Income', linestyle='--', color='blue')
        ax.plot(incomes, net, label='Net Income (After Tax & NI)', 
               color='green', linewidth=2)
        ax.fill_between(incomes, net, incomes, color='red', alpha=0.1, 
                       label='Total Tax & NI')
        ax.set_title('UK Tax Estimation (2024/25 - 2025/26)', 
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('Gross Income (£)')
        ax.set_ylabel('Amount (£)')
        ax.grid(True, alpha=0.3)
        ax.legend()
    
    def _plot_marginal_rates(self, ax, results: dict):
        """Plot marginal tax rates."""
        incomes = results['gross_income']
        marginal = results['marginal_rate']
        
        ax.plot(incomes, marginal, label='Marginal Rate (Tax + NI)', 
               color='red', linewidth=2)
        
        # Reference lines for standard rates
        ax.axhline(y=20, color='gray', linestyle=':', alpha=0.5, label='Basic rate (20%)')
        ax.axhline(y=40, color='gray', linestyle=':', alpha=0.5, label='Higher rate (40%)')
        ax.axhline(y=45, color='gray', linestyle=':', alpha=0.5, label='Additional rate (45%)')
        
        ax.set_title('Marginal Tax Rate', fontsize=14, fontweight='bold')
        ax.set_xlabel('Gross Income (£)')
        ax.set_ylabel('Marginal Rate (%)')
        ax.grid(True, alpha=0.3)
        ax.legend()
        ax.set_ylim(0, max(marginal) + 5)
        
        # Annotate peak marginal rate (60% trap)
        max_rate_idx = np.argmax(marginal)
        max_rate = marginal[max_rate_idx]
        max_rate_income = incomes[max_rate_idx]
        ax.annotate(f'Peak: {max_rate:.1f}%\n(£{max_rate_income:,.0f})', 
                   xy=(max_rate_income, max_rate), 
                   xytext=(max_rate_income + 15000, max_rate - 10),
                   arrowprops=dict(arrowstyle='->', color='red', lw=1.5),
                   fontsize=10, color='red', fontweight='bold')
