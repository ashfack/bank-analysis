
from typing import Optional, List
from pandas import DataFrame

from ..ports.loader import DataLoaderPort
from ..domain import analysis as domain_analysis
from ..domain.dto import AggregateMetrics, CategoryBreakdownRow, FilteredSummaryResult, MonthlySummaryRow

class AnalyzeBudgetUseCase:
    def __init__(self, loader: DataLoaderPort,
                 salary_category: str = domain_analysis.SALARY_CATEGORY,
                 exclude_parents: set = domain_analysis.EXCLUDE_EXPENSE_PARENTS,
                 ref_salary: float = domain_analysis.REF_THEORETICAL_SALARY):
        self.loader = loader
        self.salary_category = salary_category
        self.exclude_parents = exclude_parents
        self.ref_salary = ref_salary

    # STEP 1: Load and prepare data
    def load_data(self, csv_path: str) -> DataFrame:
        return self.loader.load_and_prepare(csv_path)

    # STEP 2: Compute monthly summary
    def compute_monthly_summary(self, df) -> List[MonthlySummaryRow]:
        return domain_analysis.compute_monthly_summary(df, self.salary_category, self.exclude_parents, self.ref_salary)

    # STEP 3: Filter atypical months
    def filter_atypical_months(self, monthly_summary) -> FilteredSummaryResult:
        return domain_analysis.filter_atypical_months(monthly_summary)

    # STEP 4: Compute aggregates
    def compute_aggregates(self, summary_df) -> AggregateMetrics:
        return domain_analysis.compute_aggregates(summary_df)

    # STEP 5: Compute category breakdown
    def compute_category_breakdown(self, df) -> List[CategoryBreakdownRow]:
        return domain_analysis.compute_category_breakdown(df, self.exclude_parents)
    
     # STEP 6: Exports
    def export(self, export_paths, summary, category_breakdown) -> None:
         # Optional export
        if export_paths and export_paths.get("summary"):
            summary.to_csv(export_paths["summary"], index=False, sep=";")
        if export_paths and export_paths.get("breakdown") and category_breakdown is not None:
            category_breakdown.to_csv(export_paths["breakdown"], index=False, sep=";")

    # Orchestration method for full workflow
    def run_full_analysis(self, csv_path: str,
                          do_filter_atypical: bool = False,
                          show_category_breakdown: bool = False,
                          export_paths: Optional[dict] = None) -> dict:
        df = self.load_data(csv_path)
        monthly_summary = self.compute_monthly_summary(df)

        if do_filter_atypical:
            filtered_summary, excluded_months = self.filter_atypical_months(monthly_summary)
        else:
            filtered_summary = monthly_summary
            excluded_months = []

        aggregates = self.compute_aggregates(filtered_summary)
        category_breakdown = None
        if show_category_breakdown:
            category_breakdown = self.compute_category_breakdown(df)

        # Optional export
        if export_paths and export_paths.get("summary"):
            filtered_summary.to_csv(export_paths["summary"], index=False, sep=";")
        if export_paths and export_paths.get("breakdown") and category_breakdown is not None:
            category_breakdown.to_csv(export_paths["breakdown"], index=False, sep=";")

        return {
            "monthly_summary": monthly_summary,
            "filtered_summary": filtered_summary,
            "excluded_months": excluded_months,
            "aggregates": aggregates,
            "category_breakdown": category_breakdown
        }
