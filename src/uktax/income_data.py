"""Data classes for UK income distribution using attrs."""
import numpy as np
import csv
from pathlib import Path
from attrs import define, field
from typing import Optional, Dict, List


@define
class IncomeDistributionData:
    """Raw income distribution data from percentiles."""
    
    percentiles: np.ndarray = field()
    incomes: np.ndarray = field()
    year: str = field(default="2023")
    
    @classmethod
    def from_list(cls, income_list, start_percentile=1, year="2023"):
        """Create from a list of incomes corresponding to consecutive percentiles."""
        percentiles = np.arange(start_percentile, start_percentile + len(income_list))
        incomes = np.array(income_list)
        return cls(percentiles=percentiles, incomes=incomes, year=year)
    
    def get_income_at_percentile(self, percentile: float) -> float:
        """Get income at a specific percentile using interpolation."""
        return np.interp(percentile, self.percentiles, self.incomes)
    
    def get_percentile_at_income(self, income: float) -> float:
        """Get percentile for a specific income using interpolation."""
        return np.interp(income, self.incomes, self.percentiles, left=0, right=100)


@define
class IncomeHistogram:
    """Histogram representation of income distribution for a population."""
    
    income_bins: np.ndarray = field()
    bin_counts: np.ndarray = field()
    population_size: int = field()
    source_data: IncomeDistributionData = field()
    
    # Derived statistics
    mean_income: float = field(init=False)
    median_income: float = field(init=False)
    bin_centers: np.ndarray = field(init=False)
    
    def __attrs_post_init__(self):
        """Calculate derived statistics after initialization."""
        self.bin_centers = (self.income_bins[:-1] + self.income_bins[1:]) / 2
        self._calculate_statistics()
    
    def _calculate_statistics(self):
        """Calculate mean and median income."""
        # Mean: weighted average of bin centers
        total_income = np.sum(self.bin_centers * self.bin_counts)
        self.mean_income = total_income / self.population_size
        
        # Median: 50th percentile from source data
        self.median_income = self.source_data.get_income_at_percentile(50)
    
    @classmethod
    def from_distribution(cls, 
                         distribution_data: IncomeDistributionData,
                         population_size: int = 100000,
                         bin_size: int = 1000,
                         max_income: Optional[int] = None):
        """Create histogram from distribution data."""
        
        if max_income is None:
            # Use maximum income from data
            max_income = int(distribution_data.incomes[-1]) + bin_size
        
        # Create income bins
        income_bins = np.arange(0, max_income + bin_size, bin_size)
        bin_counts = []
        
        # Calculate population in each bin
        for i in range(len(income_bins) - 1):
            bin_low = income_bins[i]
            bin_high = income_bins[i + 1]
            
            # Find percentiles that fall within this income bin
            percentile_low = distribution_data.get_percentile_at_income(bin_low)
            percentile_high = distribution_data.get_percentile_at_income(bin_high)
            
            # Number of people = (percentile difference / 100) * population
            people_in_bin = (percentile_high - percentile_low) / 100 * population_size
            bin_counts.append(people_in_bin)
        
        bin_counts = np.array(bin_counts)
        
        return cls(
            income_bins=income_bins,
            bin_counts=bin_counts,
            population_size=population_size,
            source_data=distribution_data
        )
    
    def get_top_percentile_bin(self, percentile: float = 99, 
                               assumed_income: Optional[float] = None):
        """
        Add a special bin for top earners beyond the data range.
        
        Args:
            percentile: The percentile beyond which data is unknown (default 99)
            assumed_income: Income to assume for plotting this bin
        """
        if assumed_income is None:
            assumed_income = self.income_bins[-1] + 4000  # For visual separation
        
        top_percent = 100 - percentile
        top_count = (top_percent / 100) * self.population_size
        
        return assumed_income, top_count


def _load_income_data_from_csv() -> Dict[str, List[int]]:
    """
    Load income distribution data from CSV file.
    
    Returns:
        Dictionary mapping tax year (e.g., "2022/23") to list of incomes for percentiles 1-99
    """
    # Find the CSV file relative to this module (go up from uktax/ to src/, then into data/)
    data_dir = Path(__file__).parent.parent / 'data'
    csv_path = data_dir / 'UK-income-before-tax.csv'
    
    income_data = {}
    
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        headers = next(reader)  # First row contains column headers
        
        # Convert column headers from "YYYY to YYYY" to "YYYY/YY" format
        # e.g., "2022 to 2023" -> "2022/23"
        tax_years = []
        for header in headers[1:]:  # Skip "Percentile" column
            header = header.strip()
            if ' to ' in header:
                parts = header.split(' to ')
                start_year = parts[0].strip()
                end_year = parts[1].strip()[-2:]  # Last 2 digits
                tax_year = f"{start_year}/{end_year}"
                tax_years.append(tax_year)
        
        # Initialize lists for each tax year
        for year in tax_years:
            income_data[year] = []
        
        # Read income data for each percentile
        for row in reader:
            if not row or not row[0].strip():
                continue
            
            # Skip percentile column (first column)
            incomes = row[1:]
            
            # Add income to each year's list
            for i, income_str in enumerate(incomes):
                if i < len(tax_years):
                    income_value = int(income_str.strip())
                    income_data[tax_years[i]].append(income_value)
    
    return income_data


# Load all income data from CSV
UK_INCOME_BY_YEAR: Dict[str, List[int]] = _load_income_data_from_csv()

# Backwards compatibility: UK_INCOME_2023 references the most recent year
UK_INCOME_2023 = UK_INCOME_BY_YEAR.get("2022/23", [])
