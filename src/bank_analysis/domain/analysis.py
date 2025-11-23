from typing import List
import pandas as pd
from .dto import MonthlySummaryRow, CategoryBreakdownRow, FilteredSummaryResult, AggregateMetrics

# Default configuration values
SALARY_CATEGORY = "Salaire fixe"
EXCLUDE_EXPENSE_PARENTS = {"Mouvements internes débiteurs", "Mouvements internes créditeurs"}
REF_THEORETICAL_SALARY = 3700.0

# ===== Computation Functions (return DTOs) =====

def compute_monthly_summary(
    df: pd.DataFrame,
    salary_category: str = SALARY_CATEGORY,
    exclude_parents: set = EXCLUDE_EXPENSE_PARENTS,
    ref_theoretical_salary: float = REF_THEORETICAL_SALARY
) -> List[MonthlySummaryRow]:
    """
    Compute monthly summary: salaries, expenses, savings.

    Returns:
        List[MonthlySummaryRow]: sorted by month ascending (YYYY-MM).
    """
    # Salaries per month
    salaries = (
        df.loc[df["category"] == salary_category]
          .groupby("month")["amount"]
          .sum()
          .rename("total_salary")
    )

    # Expenses: negative amounts, excluding internal parents
    mask_non_internal = ~df["categoryParent"].isin(exclude_parents)
    mask_neg = df["amount"] < 0
    expenses_df = df.loc[mask_non_internal & mask_neg]

    expenses = (
        expenses_df.groupby("month")["amount"]
                   .sum()
                   .abs()
                   .rename("total_expenses")
    )

    nb_ops = (
        expenses_df.groupby("month")["amount"]
                   .count()
                   .rename("nb_expense_operations")
    )

    # Combine
    out = pd.concat([salaries, expenses, nb_ops], axis=1).fillna(0.0)
    out["total_savings"] = out["total_salary"] - out["total_expenses"]
    out["total_savings_vs_theoretical"] = ref_theoretical_salary - out["total_expenses"]

    out = out.round(2).reset_index().sort_values("month")

    # Map to DTOs
    result: List[MonthlySummaryRow] = [
        MonthlySummaryRow(
            month=str(row["month"]),
            total_salary=float(row["total_salary"]),
            total_expenses=float(row["total_expenses"]),
            nb_expense_operations=int(row["nb_expense_operations"]),
            total_savings=float(row["total_savings"]),
            total_savings_vs_theoretical=float(row["total_savings_vs_theoretical"]),
        )
        for _, row in out.iterrows()
    ]
    return result


def compute_category_breakdown(
    df: pd.DataFrame,
    exclude_parents: set = EXCLUDE_EXPENSE_PARENTS
) -> List[CategoryBreakdownRow]:
    """
    Advanced mode: breakdown by category parent (total + number of operations).

    Returns:
        List[CategoryBreakdownRow]: sorted by (month, category_parent).
    """
    mask_non_internal = ~df["categoryParent"].isin(exclude_parents)
    mask_neg = df["amount"] < 0
    expenses_df = df.loc[mask_non_internal & mask_neg]

    grouped = expenses_df.groupby(["month", "categoryParent"])
    summary = grouped["amount"].agg(["sum", "count"]).reset_index()
    summary.rename(columns={"sum": "total", "count": "nb_operations"}, inplace=True)
    summary["total"] = summary["total"].abs().round(2)
    summary = summary.sort_values(["month", "categoryParent"])

    return [
        CategoryBreakdownRow(
            month=str(row["month"]),
            category_parent=str(row["categoryParent"]),
            total=float(row["total"]),
            nb_operations=int(row["nb_operations"]),
        )
        for _, row in summary.iterrows()
    ]


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
