"""UK Tax and Income Distribution Analysis Package.

This package provides tools for analyzing UK tax rates and income distribution.
"""

from uktax.income_data import (
    IncomeDistributionData, 
    IncomeHistogram, 
    UK_INCOME_2023,
    UK_INCOME_BY_YEAR
)
from uktax.uk_tax_calculator import (
    UKTaxCalculatorBase,
    UKTaxCalculatorPre2010,
    UKTaxCalculator2010,
    UKTaxCalculator2013,
    UKTaxCalculator2023,
    UKTaxCalculatorReformed,
    TaxBracket,
    optimize_additional_rate_for_revenue
)
from uktax.visualizations import (
    IncomeDistributionVisualizer, 
    TaxVisualization
)

__version__ = "0.1.0"

__all__ = [
    "IncomeDistributionData",
    "IncomeHistogram",
    "UK_INCOME_2023",
    "UK_INCOME_BY_YEAR",
    "UKTaxCalculatorBase",
    "UKTaxCalculatorPre2010",
    "UKTaxCalculator2010",
    "UKTaxCalculator2013",
    "UKTaxCalculator2023",
    "UKTaxCalculatorReformed",
    "TaxBracket",
    "optimize_additional_rate_for_revenue",
    "IncomeDistributionVisualizer",
    "TaxVisualization",
]
