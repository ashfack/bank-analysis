from enum import Enum
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


class BreakdownKind(Enum):
    """Semantic type of a breakdown row."""
    MANDATORY = "MANDATORY"
    SUPPLIER = "SUPPLIER"
    OTHER = "OTHER"
    REIMBURSEMENTS = "REIMBURSEMENTS"
    SALARY = "SALARY"


@dataclass(frozen=True)
class CategoryBreakdown:
    """
    Flat breakdown row used across the domain.
    - label: generic display label for the row; historically a category_parent,
                       but now may be a supplier name, 'Autres', 'Remboursements', or 'Salaire fixe'.
    - total: aggregated absolute amount for expenses (positive amounts for 'Salaire fixe').
    - nb_operations: number of transactions contributing to this row.
    - kind: semantic type of the row, one of:
          'MANDATORY'      -> mandatory categories (exact match, case-insensitive)
          'SUPPLIER'       -> supplier-specific rows (regex match on supplier_found)
          'OTHER'          -> other non-mandatory categories
          'REIMBURSEMENTS' -> merged reimbursements row
          'SALARY'         -> fixed salary (positive amounts only)
      Defaults to 'OTHER' for compatibility.
    """
    label: str
    total: float
    nb_operations: int
    kind:BreakdownKind = BreakdownKind.OTHER

@dataclass(frozen=True)
class AggregateMetrics:
    mean_savings: float
    mean_savings_vs_theoretical: float

@dataclass(frozen=True)
class FilteredSummary:
    filtered: List[MonthlySummary]
    excluded_months: List[str]