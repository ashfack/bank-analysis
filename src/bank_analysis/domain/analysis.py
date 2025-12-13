from collections import defaultdict
from typing import List, Final, Sequence, Set
from .dto import MonthlySummaryRow, CategoryBreakdownRow, FilteredSummaryResult, AggregateMetrics
from .entities import Transaction
from ..ports.cycle_grouper import CycleGrouper

# Default configuration values
SALARY_CATEGORY = "Salaire fixe"
EXCLUDE_EXPENSE_PARENTS:Final = frozenset({"Mouvements internes débiteurs", "Mouvements internes créditeurs"})
REF_THEORETICAL_SALARY = 3700.0

def compute_monthly_summary_core(
    txns: Sequence[Transaction],
    cycle_grouper: CycleGrouper,
    ref_theoretical_salary: float = REF_THEORETICAL_SALARY,
    salary_category: str = SALARY_CATEGORY,
    exclude_parents: frozenset[str] = EXCLUDE_EXPENSE_PARENTS,
) -> list[MonthlySummaryRow]:
    """
    Pure domain computation. Groups using the provided CycleGrouper.
    Step 1: calendar only (we'll add the salary cycle in Step 2).
    """
    salaries: dict[str, float] = defaultdict(float)
    expenses: dict[str, float] = defaultdict(float)
    ops_count: dict[str, int] = defaultdict(int)

    for t in txns:
        label = cycle_grouper.label_for_date(t.date_op)
        if t.category == salary_category:
            salaries[label] += float(t.amount)
        if t.amount < 0 and t.category_parent not in exclude_parents:
            expenses[label] += float(t.amount)  # negative sum
            ops_count[label] += 1

    groups = sorted(set(salaries) | set(expenses))
    out: list[MonthlySummaryRow] = []
    for g in groups:
        total_salary = round(salaries.get(g, 0.0), 2)
        total_expenses = round(abs(expenses.get(g, 0.0)), 2)  # abs of negative sum
        nb_ops = ops_count.get(g, 0)

        total_savings = round(total_salary - total_expenses, 2)
        total_vs_theoretical = round(ref_theoretical_salary - total_expenses, 2)

        out.append(MonthlySummaryRow(
            month=g,
            total_salary=total_salary,
            total_expenses=total_expenses,
            nb_expense_operations=nb_ops,
            total_savings=total_savings,
            total_savings_vs_theoretical=total_vs_theoretical,
        ))
    return out



def compute_category_breakdown(
    transactions: Sequence[Transaction],
    exclude_parents: Set[str] = EXCLUDE_EXPENSE_PARENTS
) -> List[CategoryBreakdownRow]:
    """
    Advanced mode: breakdown by category parent (total + number of operations):
      - filters out parents in exclude_parents
      - considers only expenses (amount < 0)
      - sums absolute values of expenses per category_parent
      - counts operations per category_parent
      - sorts by category_parent

    Returns:
        List[CategoryBreakdownRow]: sorted by category_parent.
    """
    totals = defaultdict(float)
    counts = defaultdict(int)

    for tx in transactions:
        # Skip if category_parent is missing
        cp = tx.category_parent
        if cp is None:
            continue

        # Filter non-internal (not in excluded list) and negative amounts (expenses)
        if cp not in exclude_parents and tx.amount < 0:
            # Accumulate absolute value (equivalent to pandas .abs() on the sum)
            totals[cp] += -tx.amount
            counts[cp] += 1

    # Build rows sorted by category_parent, and round totals to 2 decimals
    rows = [
        CategoryBreakdownRow(
            category_parent=cp,
            total=round(totals[cp], 2),
            nb_operations=counts[cp],
        )
        for cp in sorted(totals.keys())
    ]

    return rows



def filter_atypical_months(
    summary: List[MonthlySummaryRow]
) -> FilteredSummaryResult:
    """
    Exclude months with negative savings or negative theoretical delta.

    Args:
        summary: List of MonthlySummaryRow DTOs.

    Returns:
        FilteredSummaryResult(filtered=[...], excluded_months=[...])
    """
    excluded_months = [
        s.month for s in summary
        if (s.total_savings < 0) or (s.total_savings_vs_theoretical < 0)
    ]
    filtered = [s for s in summary if s.month not in excluded_months]
    return FilteredSummaryResult(filtered=filtered, excluded_months=excluded_months)


def compute_aggregates(summary: List[MonthlySummaryRow]) -> AggregateMetrics:
    """
    Compute aggregate averages from DTOs.

    Args:
        summary: List of MonthlySummaryRow DTOs (e.g., filtered summary).

    Returns:
        AggregateMetrics(mean_savings=..., mean_savings_vs_theoretical=...)
    """
    if not summary:
        return AggregateMetrics(mean_savings=0.0, mean_savings_vs_theoretical=0.0)

    mean_savings = sum(s.total_savings for s in summary) / len(summary)
    mean_theoretical = sum(s.total_savings_vs_theoretical for s in summary) / len(summary)
    return AggregateMetrics(
        mean_savings=round(float(mean_savings), 2),
        mean_savings_vs_theoretical=round(float(mean_theoretical), 2),
    )
