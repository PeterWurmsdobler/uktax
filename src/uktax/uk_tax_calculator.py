"""UK Tax Calculator using 2024/25 - 2025/26 parameters."""
import numpy as np
from abc import ABC, abstractmethod
from attrs import define, field
from typing import Tuple
from scipy.optimize import brentq


@define
class TaxBracket:
    """Represents a tax bracket with threshold and rate."""
    threshold: float
    rate: float
    name: str


class TaperablePAMixin:
    """Mixin providing personal allowance tapering logic.
    
    Classes using this mixin must define:
    - personal_allowance: float
    - taper_threshold: float  
    - taper_rate: float
    """
    
    def calculate_personal_allowance(self, gross_income: float) -> float:
        """Calculate personal allowance including tapering for high earners.
        
        Implements the standard UK PA taper: £1 lost per £2 over threshold.
        """
        if gross_income <= self.taper_threshold:
            return self.personal_allowance
        
        reduction = (gross_income - self.taper_threshold) * self.taper_rate
        return max(0, self.personal_allowance - reduction)


@define
class UKTaxCalculatorBase(ABC):
    """Base class for UK income tax and National Insurance calculators."""
    
    # Tax parameters for 2024/25 - 2025/26 (Rest of UK)
    personal_allowance: float = field(default=12570)
    basic_rate_threshold: float = field(default=50270)
    higher_rate_threshold: float = field(default=125140)
    
    basic_rate: float = field(default=0.20)
    higher_rate: float = field(default=0.40)
    additional_rate: float = field(default=0.45)
    
    # National Insurance thresholds and rates
    ni_lower_threshold: float = field(default=12570)
    ni_upper_threshold: float = field(default=50270)
    ni_standard_rate: float = field(default=0.08)
    ni_higher_rate: float = field(default=0.02)
    
    @abstractmethod
    def calculate_personal_allowance(self, gross_income: float) -> float:
        """
        Calculate personal allowance. 
        Must be overridden by subclasses to implement specific rules.
        """
        pass
    
    def calculate_income_tax(self, gross_income: float) -> float:
        """Calculate income tax for a given gross income.
        
        UK tax system uses:
        - Basic rate band: defined on TAXABLE income
        - Additional rate: defined on GROSS income
        """
        personal_allowance = self.calculate_personal_allowance(gross_income)
        taxable_income = max(0, gross_income - personal_allowance)
        
        if taxable_income <= 0:
            return 0
        
        # Basic rate band calculation: varies by period based on PA at zero income
        # For someone with full PA, the basic_rate_threshold is where they hit higher rate
        # So basic_taxable_limit = basic_rate_threshold - full_PA
        full_personal_allowance = self.calculate_personal_allowance(0)  # PA at zero income
        basic_taxable_limit = self.basic_rate_threshold - full_personal_allowance
        
        # Additional rate threshold is £125,140 of GROSS income
        # Check if we're in the additional rate band
        if gross_income > self.higher_rate_threshold:
            # Additional rate applies to gross income above £125,140
            additional_income = gross_income - self.higher_rate_threshold
            # tax on income from PA to basic limit
            basic_tax = basic_taxable_limit * self.basic_rate
            # tax on income from basic limit to additional rate threshold (gross)
            higher_taxable = (self.higher_rate_threshold - personal_allowance) - basic_taxable_limit
            higher_tax = higher_taxable * self.higher_rate
            # tax on income above additional rate threshold
            additional_tax = additional_income * self.additional_rate
            return basic_tax + higher_tax + additional_tax
        elif taxable_income <= basic_taxable_limit:
            # Entirely in basic rate band
            return taxable_income * self.basic_rate
        else:
            # In higher rate band only
            return (basic_taxable_limit * self.basic_rate + 
                   (taxable_income - basic_taxable_limit) * self.higher_rate)
    
    def calculate_national_insurance(self, gross_income: float) -> float:
        """Calculate National Insurance contributions (Category A)."""
        if gross_income <= self.ni_lower_threshold:
            return 0
        elif gross_income <= self.ni_upper_threshold:
            return (gross_income - self.ni_lower_threshold) * self.ni_standard_rate
        else:
            standard_band = (self.ni_upper_threshold - self.ni_lower_threshold) * self.ni_standard_rate
            higher_band = (gross_income - self.ni_upper_threshold) * self.ni_higher_rate
            return standard_band + higher_band
    
    def calculate_total_deductions(self, gross_income: float) -> Tuple[float, float, float]:
        """
        Calculate total deductions (tax + NI) and net income.
        
        Returns:
            Tuple of (total_deductions, income_tax, national_insurance)
        """
        tax = self.calculate_income_tax(gross_income)
        ni = self.calculate_national_insurance(gross_income)
        total = tax + ni
        return total, tax, ni
    
    def calculate_net_income(self, gross_income: float) -> float:
        """Calculate net income after tax and NI."""
        total_deductions, _, _ = self.calculate_total_deductions(gross_income)
        return gross_income - total_deductions
    
    def calculate_marginal_rate(self, gross_income: float, delta: float = 1.0) -> float:
        """
        Calculate marginal tax rate (tax + NI on next £1 earned).
        
        Returns:
            Marginal rate as a percentage
        """
        current_deductions, _, _ = self.calculate_total_deductions(gross_income)
        next_deductions, _, _ = self.calculate_total_deductions(gross_income + delta)
        marginal_rate = (next_deductions - current_deductions) / delta
        return marginal_rate * 100
    
    def calculate_effective_rate(self, gross_income: float) -> float:
        """
        Calculate effective tax rate (total deductions / gross income).
        
        Returns:
            Effective rate as a percentage
        """
        if gross_income == 0:
            return 0
        total_deductions, _, _ = self.calculate_total_deductions(gross_income)
        return (total_deductions / gross_income) * 100
    
    def calculate_for_range(self, income_range: np.ndarray) -> dict:
        """
        Calculate tax metrics for a range of incomes.
        
        Returns:
            Dictionary with arrays for various tax metrics
        """
        results = {
            'gross_income': income_range,
            'total_deductions': np.array([self.calculate_total_deductions(i)[0] for i in income_range]),
            'income_tax': np.array([self.calculate_total_deductions(i)[1] for i in income_range]),
            'national_insurance': np.array([self.calculate_total_deductions(i)[2] for i in income_range]),
            'net_income': np.array([self.calculate_net_income(i) for i in income_range]),
            'marginal_rate': np.array([self.calculate_marginal_rate(i) for i in income_range]),
            'effective_rate': np.array([self.calculate_effective_rate(i) for i in income_range])
        }
        return results


@define
class UKTaxCalculatorPre2010(UKTaxCalculatorBase):
    """
    UK tax calculator for pre-April 2010 (Period 1: The Two-Band Era).
    
    Characteristics:
    - Personal allowance: £6,475 (no taper)
    - Two income tax bands: 20% and 40%
    - No additional rate band
    - NI: 11% up to UEL, 1% above
    """
    
    # Override default parameters for this period
    personal_allowance: float = field(default=6475)
    basic_rate_threshold: float = field(default=37400 + 6475)  # £37,400 taxable + PA
    higher_rate_threshold: float = field(default=float('inf'))  # No additional rate
    
    basic_rate: float = field(default=0.20)
    higher_rate: float = field(default=0.40)
    additional_rate: float = field(default=0.40)  # Same as higher (no separate band)
    
    # National Insurance thresholds and rates for this period
    ni_lower_threshold: float = field(default=5715)
    ni_upper_threshold: float = field(default=43875)  # UEL
    ni_standard_rate: float = field(default=0.11)
    ni_higher_rate: float = field(default=0.01)
    
    def calculate_personal_allowance(self, gross_income: float) -> float:
        """Calculate personal allowance - constant (no tapering in this period)."""
        return self.personal_allowance


@define
class UKTaxCalculator2010(TaperablePAMixin, UKTaxCalculatorBase):
    """
    UK tax calculator for 2010-2013 (Period 2: Introduction of Additional Rate).
    
    Characteristics:
    - Personal allowance: £6,475 (with taper starting at £100,000)
    - Three income tax bands: 20%, 40%, 50%
    - Additional rate (50%) starts at £150,000
    - NI: 12% up to UEL, 2% above (increased in 2011)
    """
    
    # Override default parameters for this period
    personal_allowance: float = field(default=6475)
    basic_rate_threshold: float = field(default=37400 + 6475)  # £37,400 taxable + PA = £43,875 (same as Pre-2010)
    higher_rate_threshold: float = field(default=150000)  # Additional rate starts at £150k
    
    basic_rate: float = field(default=0.20)
    higher_rate: float = field(default=0.40)
    additional_rate: float = field(default=0.50)  # New 50% top rate
    
    # Tapering parameters (introduced in this period)
    taper_threshold: float = field(default=100000)
    taper_rate: float = field(default=0.5)
    
    # National Insurance thresholds and rates for this period
    ni_lower_threshold: float = field(default=5715)  # Primary Threshold 2010/11
    ni_upper_threshold: float = field(default=37400 + 6475)  # UEL aligned with basic rate threshold = £43,875
    ni_standard_rate: float = field(default=0.12)  # Increased from 11%
    ni_higher_rate: float = field(default=0.02)  # Increased from 1%


@define
class UKTaxCalculator2013(TaperablePAMixin, UKTaxCalculatorBase):
    """
    UK tax calculator for 2013-2023 (Period 3: The 45% Adjustment Era).
    
    Characteristics:
    - Personal allowance: £12,570 (by 2021, with taper at £100,000)
    - Three income tax bands: 20%, 40%, 45%
    - Additional rate reduced from 50% to 45%
    - Additional rate starts at £150,000
    - NI: 12% up to £50,270, 2% above
    """
    
    # Override default parameters for this period
    personal_allowance: float = field(default=12570)
    basic_rate_threshold: float = field(default=37700 + 12570)  # £37,700 taxable + PA = £50,270
    higher_rate_threshold: float = field(default=150000)  # Additional rate starts at £150k
    
    basic_rate: float = field(default=0.20)
    higher_rate: float = field(default=0.40)
    additional_rate: float = field(default=0.45)  # Reduced from 50%
    
    # Tapering parameters
    taper_threshold: float = field(default=100000)
    taper_rate: float = field(default=0.5)
    
    # National Insurance thresholds and rates for this period
    ni_lower_threshold: float = field(default=12570)
    ni_upper_threshold: float = field(default=50270)  # UEL
    ni_standard_rate: float = field(default=0.12)
    ni_higher_rate: float = field(default=0.02)


@define
class UKTaxCalculator2023(TaperablePAMixin, UKTaxCalculatorBase):
    """
    UK tax calculator for 2023-present (Period 4: The Alignment Era).
    
    Characteristics:
    - Personal allowance: £12,570 (with taper at £100,000, gone by £125,140)
    - Three income tax bands: 20%, 40%, 45%
    - Additional rate NOW starts at £125,140 (aligned with end of taper)
    - NI: 8% up to £50,270, 2% above (cut from 12% in 2024)
    
    This creates the infamous 60% marginal rate trap between £100,000 and £116,760.
    """
    
    # Tax parameters for 2024/25 - 2025/26 (Rest of UK)
    personal_allowance: float = field(default=12570)
    basic_rate_threshold: float = field(default=50270)
    higher_rate_threshold: float = field(default=125140)
    
    basic_rate: float = field(default=0.20)
    higher_rate: float = field(default=0.40)
    additional_rate: float = field(default=0.45)
    
    # Tapering parameters (creates the 60% trap)
    taper_threshold: float = field(default=100000)
    taper_rate: float = field(default=0.5)
    
    # National Insurance thresholds and rates
    ni_lower_threshold: float = field(default=12570)
    ni_upper_threshold: float = field(default=50270)
    ni_standard_rate: float = field(default=0.08)  # Cut from 12%
    ni_higher_rate: float = field(default=0.02)


@define
class UKTaxCalculatorReformed(UKTaxCalculatorBase):
    """Reformed UK tax calculator with no personal allowance tapering but adjustable additional rate."""
    
    # No tapering in reformed version - personal allowance stays constant
    # Higher rate threshold set at £100,000 (gross income)
    # This is where the 60% trap begins in the classic system
    higher_rate_threshold: float = field(default=100000)
    
    def calculate_personal_allowance(self, gross_income: float) -> float:
        """Calculate personal allowance - constant, no tapering."""
        return self.personal_allowance


def optimize_additional_rate_for_revenue(target_revenue: float, 
                                         histogram, 
                                         top_percentile_income: float = None,
                                         initial_guess: float = 0.45,
                                         tolerance: float = 1e-6) -> Tuple[float, float]:
    """
    Find the additional rate for UKTaxCalculatorReformed that matches target revenue.
    
    Args:
        target_revenue: Target total tax revenue to match
        histogram: Income histogram for population
        top_percentile_income: Assumed income for top 1% (if None, calculated as max_income * 1.15)
        initial_guess: Starting guess for additional rate
        tolerance: Tolerance for optimization
        
    Returns:
        Tuple of (optimal_additional_rate, achieved_revenue)
    """
    from uktax.income_data import IncomeHistogram
    
    # Calculate top percentile income from histogram if not provided
    # Use conservative assumption: top 1% earn at least the 99th percentile value
    if top_percentile_income is None:
        max_known_income = histogram.source_data.incomes[-1]
        top_percentile_income = max_known_income  # Conservative: minimum income for top 1%
    
    def calculate_revenue_with_rate(additional_rate: float) -> float:
        """Calculate total revenue for a given additional rate."""
        calculator = UKTaxCalculatorReformed(additional_rate=additional_rate)
        total_revenue = 0
        
        for i in range(len(histogram.bin_counts)):
            income = histogram.bin_centers[i]
            people = histogram.bin_counts[i]
            
            # Handle top percentile separately
            max_known_income = histogram.source_data.incomes[-1]
            if income > max_known_income:
                income = top_percentile_income
            
            deductions, _, _ = calculator.calculate_total_deductions(income)
            total_revenue += deductions * people
        
        return total_revenue
    
    def revenue_difference(additional_rate: float) -> float:
        """Objective function: difference from target revenue."""
        return calculate_revenue_with_rate(additional_rate) - target_revenue
    
    # Find the rate that gives us the target revenue
    # Search between 0.3 and 0.7 (30% to 70%)
    try:
        optimal_rate = brentq(revenue_difference, 0.30, 0.70, xtol=tolerance)
        achieved_revenue = calculate_revenue_with_rate(optimal_rate)
        return optimal_rate, achieved_revenue
    except ValueError as e:
        # If we can't find a solution in the range, try with wider bounds
        print(f"Warning: Could not find solution in [0.30, 0.70], trying wider range...")
        try:
            optimal_rate = brentq(revenue_difference, 0.20, 0.80, xtol=tolerance)
            achieved_revenue = calculate_revenue_with_rate(optimal_rate)
            return optimal_rate, achieved_revenue
        except ValueError:
            print(f"Error: Could not find additional rate to match target revenue")
            raise


def optimize_additional_rate_no_losers(classic_calculator,
                                       histogram, 
                                       top_percentile_income: float = 202000,
                                       tolerance: float = 1e-6) -> Tuple[float, float]:
    """
    Find the additional rate where people in the trap benefit, but high earners are neutral.
    
    Strategy: Find the rate where taxes at a high income (£150k) match the classic system.
    This ensures people in the trap (£100k-£116k) benefit while high earners stay neutral.
    
    Args:
        classic_calculator: Classic calculator to compare against
        histogram: Income histogram for population
        top_percentile_income: Assumed income for top 1%
        tolerance: Tolerance for optimization
        
    Returns:
        Tuple of (optimal_additional_rate, achieved_revenue)
    """
    from uktax.income_data import IncomeHistogram
    
    # Choose a high income point where we want taxes to match (above the trap)
    target_income = 150000  # Well above the trap zone
    
    def tax_difference_at_target(additional_rate: float) -> float:
        """
        Calculate tax difference at target income.
        Returns reformed_tax - classic_tax.
        We want this to be zero (neutral for high earners).
        """
        reformed_calc = UKTaxCalculatorReformed(additional_rate=additional_rate)
        
        classic_tax = classic_calculator.calculate_total_deductions(target_income)[0]
        reformed_tax = reformed_calc.calculate_total_deductions(target_income)[0]
        
        return reformed_tax - classic_tax
    
    # Find the rate where taxes match at target income
    # Search between 0.30 and 0.50 (30% to 50%)
    try:
        optimal_rate = brentq(tax_difference_at_target, 0.30, 0.50, xtol=tolerance)
    except ValueError:
        # If no solution in range, try wider bounds
        try:
            optimal_rate = brentq(tax_difference_at_target, 0.20, 0.60, xtol=tolerance)
        except ValueError:
            # Fall back to a reasonable default
            optimal_rate = 0.40
    
    # Calculate revenue with optimal rate
    reformed_calc = UKTaxCalculatorReformed(additional_rate=optimal_rate)
    total_revenue = 0
    
    for i in range(len(histogram.bin_counts)):
        income = histogram.bin_centers[i]
        people = histogram.bin_counts[i]
        
        max_known_income = histogram.source_data.incomes[-1]
        if income > max_known_income:
            income = top_percentile_income
        
        deductions, _, _ = reformed_calc.calculate_total_deductions(income)
        total_revenue += deductions * people
    
    return optimal_rate, total_revenue
