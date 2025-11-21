from typing import Tuple
from dataclasses import dataclass
import pandas as pd

# Default configuration values
SALARY_CATEGORY = "Salaire fixe"
EXCLUDE_EXPENSE_PARENTS = {"Mouvements internes débiteurs", "Mouvements internes créditeurs"}
REF_THEORETICAL_SALARY = 3700.0

@dataclass
class AggregateMetrics:
    mean_savings: float
    mean_savings_vs_theoretical: float

def compute_monthly_summary(df: pd.DataFrame,
                            salary_category: str = SALARY_CATEGORY,
                            exclude_parents: set = EXCLUDE_EXPENSE_PARENTS,
                            ref_theoretical_salary: float = REF_THEORETICAL_SALARY) -> pd.DataFrame:
    """Compute monthly summary: salaries, expenses, savings."""
    salaries = df.loc[df["category"] == salary_category].groupby("month")["amount"].sum().rename("total_salary")
    mask_non_internal = ~df["categoryParent"].isin(exclude_parents)
    mask_neg = df["amount"] < 0
    expenses_df = df.loc[mask_non_internal & mask_neg]
    expenses = expenses_df.groupby("month")["amount"].sum().abs().rename("total_expenses")
    nb_ops = expenses_df.groupby("month")["amount"].count().rename("nb_expense_operations")
    out = pd.concat([salaries, expenses, nb_ops], axis=1).fillna(0.0)
    out["total_savings"] = out["total_salary"] - out["total_expenses"]
    out["total_savings_vs_theoretical"] = ref_theoretical_salary - out["total_expenses"]
    return out.round(2).reset_index().sort_values("month")

def compute_category_breakdown(df: pd.DataFrame,
                               exclude_parents: set = EXCLUDE_EXPENSE_PARENTS) -> pd.DataFrame:
    """Advanced mode: breakdown by category parent (total + number of operations)."""
    mask_non_internal = ~df["categoryParent"].isin(exclude_parents)
    mask_neg = df["amount"] < 0
    expenses_df = df.loc[mask_non_internal & mask_neg]
    grouped = expenses_df.groupby(["month", "categoryParent"])
    summary = grouped["amount"].agg(["sum", "count"]).reset_index()
    summary.rename(columns={"sum": "total", "count": "nb_operations"}, inplace=True)
    summary["total"] = summary["total"].abs().round(2)
    return summary.sort_values(["month", "categoryParent"])

def filter_atypical_months(summary_df: pd.DataFrame) -> Tuple[pd.DataFrame, list]:
    """Exclude months with negative savings or deviation."""
    excluded_months = summary_df.loc[
        (summary_df["total_savings"] < 0) | (summary_df["total_savings_vs_theoretical"] < 0),
        "month"
    ].tolist()
    filtered_df = summary_df[~summary_df["month"].isin(excluded_months)]
    return filtered_df, excluded_months

def compute_aggregates(summary_df: pd.DataFrame) -> AggregateMetrics:
    """Compute aggregate averages."""
    if summary_df.empty:
        return AggregateMetrics(mean_savings=0.0, mean_savings_vs_theoretical=0.0)
    return AggregateMetrics(
        mean_savings=float(summary_df["total_savings"].mean()),
        mean_savings_vs_theoretical=float(summary_df["total_savings_vs_theoretical"].mean())
    )