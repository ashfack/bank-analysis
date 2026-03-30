from dataclasses import dataclass
from enum import Enum

from typing import List, Dict
import pandas as pd

@dataclass(frozen=True)
class Transaction:
    """The formal definition of a single financial movement."""
    dateOperation: pd.Timestamp
    label: str
    amount: float
    category: str

@dataclass(frozen=True)
class BudgetDomain:
    """The complete 'Input State' for the Orchestrator."""
    transactions: List[Transaction]
    category_cluster_map: Dict[str, str]
    budget_overrides: Dict[str, str]

class ClusterLabel(str, Enum):
    """
    Standardized labels for financial categorization.
    Using str inheritance for easy JSON/Excel serialization.
    """
    INTERNAL = "0. Internal"
    INCOMING = "0. Incoming"
    CORE = "1. Core"
    OTHER_RECURRING = "4. Other Recurring"
    OTHER_PUNCTUAL = "4. Other Punctual"
    EXCEPTIONAL = "5. Exceptional"

@dataclass(frozen=True)
class CategoryStats:
    """
    Data Transfer Object representing statistical metrics for a category.
    
    Attributes:
        median (float): The median amount of transactions in this category.
        std (float): The standard deviation of amounts.
        count (int): Total number of transactions.
        frequency (float): Occurrences divided by total number of cycles.
    """
    median: float
    std: float
    count: int
    frequency: float

    @property
    def cv(self) -> float:
        """Calculates the Coefficient of Variation (Stability Index)."""
        return (self.std / self.median) if self.median > 0 else 0.0


@dataclass(frozen=True)
class BudgetResult:
    """
    The final output structure for a budgeted category.

    Attributes:
        category: The name of the category.
        master_cluster: The assigned cluster label.
        base_limit: The initial limit calculated by the strategy.
        theoretical_budget: The final limit after overrides and caps.
        actual_spending: The total absolute amount spent in the period.
    """
    category: str
    master_cluster: ClusterLabel
    base_limit: float
    theoretical_budget: float
    actual_spending: float

@dataclass(frozen=True)
class StrategyConfig:
    """
    Explicit configuration for budget calculation strategies.
    
    Attributes:
        percentile_target: The historical data point (0-100) to target.
        safety_multiplier: The 'buffer' factor applied to the base result (e.g., 1.1 for +10%).
        volatility_sensitivity: How many standard deviations to allow for Z-score strategies.
        histogram_bins: The resolution of the frequency distribution for mode detection.
    """
    percentile_target: int = 75
    safety_multiplier: float = 1.1
    volatility_sensitivity: float = 0.8
    histogram_bins: int = 10

@dataclass(frozen=True)
class ProcessedCategory:
    """The final calculated result for a single category."""
    category: str
    master_cluster: str
    median: float
    std_dev: float
    count: int
    frequency: float
    base_limit: float
    theoretical_budget: float
    total_actual_spending: float