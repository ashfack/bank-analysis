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

@dataclass(frozen=True)
class BudgetView:
    """
    A Pure Domain Object representing the final 'Pilotage' state.
    Uses standard Python types to remain infrastructure-agnostic.
    """
    # { "Cycle_Date": { "Cluster_Name": Amount } }
    matrix: Dict[str, Dict[str, float]]
    # { "Cluster_Name": Theoretical_Budget }
    cluster_budgets: Dict[str, float]
    processed_categories: List[ProcessedCategory]

    @property
    def cycles(self) -> List[str]:
        return sorted(self.matrix.keys(), reverse=True)

    @property
    def clusters(self) -> List[str]:
        return sorted(self.cluster_budgets.keys())

    def get_amount(self, cycle: str, cluster: str) -> float:
        return self.matrix.get(cycle, {}).get(cluster, 0.0)
    
    def get_budget(self, cluster: str) -> float:
        return self.cluster_budgets.get(cluster, 0.0)
