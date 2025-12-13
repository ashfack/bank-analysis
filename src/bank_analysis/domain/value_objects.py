
from typing import List
from dataclasses import dataclass


# ===== Domain DTOs =====

@dataclass(frozen=True)
class MonthlySummary:
    month: str
    total_salary: float
    total_expenses: float
    nb_expense_operations: int
    total_savings: float
    total_savings_vs_theoretical: float

@dataclass(frozen=True)
class CategoryBreakdown:
    category_parent: str
    total: float
    nb_operations: int

@dataclass(frozen=True)
class AggregateMetrics:
    mean_savings: float
    mean_savings_vs_theoretical: float

@dataclass(frozen=True)
class FilteredSummary:
    filtered: List[MonthlySummary]
    excluded_months: List[str]