from typing import Optional, Protocol
import pandas as pd
from ..ports.presenter import PresenterPort
from ..ports.loader import DataLoaderPort
from ..domain import analysis as domain_analysis

class AnalyzeBudgetUseCase:
    def __init__(self, loader: DataLoaderPort, presenter: PresenterPort,
                 salary_category: str = domain_analysis.SALARY_CATEGORY,
                 exclude_parents: set = domain_analysis.EXCLUDE_EXPENSE_PARENTS,
                 ref_salary: float = domain_analysis.REF_THEORETICAL_SALARY):
        self.loader = loader
        self.presenter = presenter
        self.salary_category = salary_category
        self.exclude_parents = exclude_parents
        self.ref_salary = ref_salary

    def run_from_path(self, csv_path: str, do_filter_atypical: bool = False, show_category_breakdown: bool = False,
                      export_paths: Optional[dict] = None) -> dict:
        df = self.loader.load_and_prepare(csv_path)
        monthly_summary = domain_analysis.compute_monthly_summary(df, self.salary_category, self.exclude_parents, self.ref_salary)
        self.presenter.present_monthly_summary(monthly_summary)

        if do_filter_atypical:
            filtered_summary, excluded = domain_analysis.filter_atypical_months(monthly_summary)
            self.presenter.present_filtered_summary(filtered_summary, excluded)
            calc_df = filtered_summary
            excluded_months = excluded
        else:
            calc_df = monthly_summary
            excluded_months = []

        aggregates = domain_analysis.compute_aggregates(calc_df)
        self.presenter.present_aggregates(aggregates)

        category_breakdown = None
        if show_category_breakdown:
            category_breakdown = domain_analysis.compute_category_breakdown(df, self.exclude_parents)
            self.presenter.present_category_breakdown(category_breakdown)

        if export_paths and export_paths.get("summary") is not None:
            calc_df.to_csv(export_paths["summary"], index=False, sep=";")
        if export_paths and export_paths.get("breakdown") is not None and category_breakdown is not None:
            category_breakdown.to_csv(export_paths["breakdown"], index=False, sep=";")

        return {
            "monthly_summary": monthly_summary,
            "filtered_summary": calc_df,
            "excluded_months": excluded_months,
            "aggregates": aggregates,
            "category_breakdown": category_breakdown
        }