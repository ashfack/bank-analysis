
from typing import List, Tuple
import pandas as pd
from .dto import MonthlySummaryRow, CategoryBreakdownRow, FilteredSummaryResult, AggregateMetrics

# Default configuration values
SALARY_CATEGORY = "Salaire fixe"
EXCLUDE_EXPENSE_PARENTS = {"Mouvements internes débiteurs", "Mouvements internes créditeurs"}
REF_THEORETICAL_SALARY = 3700.0

# ===== Helpers for Salary Cycle =====

def build_salary_periods(df: pd.DataFrame, salary_category: str) -> List[Tuple[pd.Timestamp, pd.Timestamp]]:
    """
    Build dynamic salary periods based on actual salary transaction dates.
    Each period starts on a salary date and ends the day before the next salary date.
    """
    salary_dates = sorted(df.loc[df["category"] == salary_category, "dateOp"].unique())
    if not salary_dates:
        return []
    periods = []
    for i in range(len(salary_dates) - 1):
        start = pd.Timestamp(salary_dates[i])
        end = pd.Timestamp(salary_dates[i + 1]) - pd.Timedelta(days=1)
        periods.append((start, end))
    # Last period until max date in dataset
    periods.append((pd.Timestamp(salary_dates[-1]), df["dateOp"].max()))
    return periods


def assign_salary_period(row_date: pd.Timestamp, periods: List[Tuple[pd.Timestamp, pd.Timestamp]]) -> str:
    for start, end in periods:
        if start <= row_date <= end:
            return f"{start.date()} to {end.date()}"
    return "Outside salary periods"


# ===== Computation Functions (return DTOs) =====

def compute_monthly_summary(
    df: pd.DataFrame,
    salary_category: str = SALARY_CATEGORY,
    exclude_parents: set = EXCLUDE_EXPENSE_PARENTS,
    ref_theoretical_salary: float = REF_THEORETICAL_SALARY,
    cycle: str = "calendar"  # NEW: "calendar" or "salary"
) -> List[MonthlySummaryRow]:
    """
    Compute summary: salaries, expenses, savings.
    Supports calendar months or salary-to-salary cycles.

    Args:
        df: DataFrame with columns ["dateOp", "month", "category", "categoryParent", "amount"]
        cycle: "calendar" (default) or "salary"

    Returns:
        List[MonthlySummaryRow]: sorted by period ascending.
    """
    # Determine grouping key
    if cycle == "salary":
        periods = build_salary_periods(df, salary_category)
        df["salary_period"] = df["dateOp"].apply(lambda d: assign_salary_period(d, periods))
        group_key = "salary_period"
    else:
        group_key = "month"

    # Salaries per period
    salaries = (
        df.loc[df["category"] == salary_category]
          .groupby(group_key)["amount"]
          .sum()
          .rename("total_salary")
    )

    # Expenses: negative amounts, excluding internal parents
    mask_non_internal = ~df["categoryParent"].isin(exclude_parents)
    mask_neg = df["amount"] < 0
    expenses_df = df.loc[mask_non_internal & mask_neg]

    expenses = (
        expenses_df.groupby(group_key)["amount"]
                   .sum()
                   .abs()
                   .rename("total_expenses")
    )

    nb_ops = (
        expenses_df.groupby(group_key)["amount"]
                   .count()
                   .rename("nb_expense_operations")
    )

    # Combine
    out = pd.concat([salaries, expenses, nb_ops], axis=1).fillna(0.0)
    out["total_savings"] = out["total_salary"] - out["total_expenses"]
    out["total_savings_vs_theoretical"] = ref_theoretical_salary - out["total_expenses"]

    out = out.round(2).reset_index().sort_values(group_key)

    # Map to DTOs
    result: List[MonthlySummaryRow] = [
        MonthlySummaryRow(
            month=str(row[group_key]),
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
