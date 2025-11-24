
from typing import Optional, List
from pandas import DataFrame

from .compute_aggregates import ComputeAggregatesUseCase
from .compute_category_breakdown import ComputeCategoryBreakdownUseCase
from .compute_monthly_summary import ComputeMonthlySummaryUseCase
from .data_loading import DataLoadingUseCase
from .filter_atypical_months import FilterAtypicalMonthsUseCase
from ..ports.cycle_grouper import CycleGrouper
from ..ports.loader import DataLoaderPort
from ..domain import analysis as domain_analysis
from ..domain.dto import AggregateMetrics, CategoryBreakdownRow, FilteredSummaryResult, MonthlySummaryRow

class FullGlobalAnalysisUseCase:
    def __init__(self, loader: DataLoaderPort,
                 cycle_grouper: CycleGrouper,
                 salary_category: str = domain_analysis.SALARY_CATEGORY,
                 exclude_parents: set = domain_analysis.EXCLUDE_EXPENSE_PARENTS,
                 ref_salary: float = domain_analysis.REF_THEORETICAL_SALARY):
        self.loader = loader
        self.cycle_grouper = cycle_grouper
        self.salary_category = salary_category
        self.exclude_parents = exclude_parents
        self.ref_salary = ref_salary

    # Orchestration method for full workflow
    def run_full_analysis(self, csv_path: str, cycle: str = "calendar" ,
                          do_filter_atypical: bool = False,
                          show_category_breakdown: bool = False,
                          export_paths: Optional[dict] = None) -> dict:

        data_loader_uc = DataLoadingUseCase(self.loader)
        monthly_summary_uc = ComputeMonthlySummaryUseCase(self.cycle_grouper)
        filter_uc = FilterAtypicalMonthsUseCase()
        aggregates_uc = ComputeAggregatesUseCase()
        category_breakdown_uc = ComputeCategoryBreakdownUseCase()

        df = data_loader_uc.execute(csv_path)
        monthly_summary = monthly_summary_uc.execute(df, cycle)

        if do_filter_atypical:
            filtered_summary_result  = filter_uc.execute(monthly_summary)
            filtered_summary = filtered_summary_result.filtered
            excluded_months = filtered_summary_result.excluded_months
        else:
            filtered_summary = monthly_summary
            excluded_months = []

        aggregates = aggregates_uc.execute(filtered_summary)
        category_breakdown = None
        if show_category_breakdown:
            category_breakdown = category_breakdown_uc.execute(df)

        return {
            "monthly_summary": monthly_summary,
            "filtered_summary": filtered_summary,
            "excluded_months": excluded_months,
            "aggregates": aggregates,
            "category_breakdown": category_breakdown
        }
