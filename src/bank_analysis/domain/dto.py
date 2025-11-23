
from typing import List
from dataclasses import dataclass


# ===== Domain DTOs =====

@dataclass(frozen=True)
class MonthlySummaryRow:
    month: str
    total_salary: float
    total_expenses: float
    nb_expense_operations: int
    total_savings: float
    total_savings_vs_theoretical: float

@dataclass(frozen=True)
class CategoryBreakdownRow:
    month: str
    category_parent: str
    total: float
    nb_operations: int

@dataclass(frozen=True)
class AggregateMetrics:
    mean_savings: float
    mean_savings_vs_theoretical: float

@dataclass(frozen=True)
class FilteredSummaryResult:
    filtered: List[MonthlySummaryRow]
    excluded_months: List[str]