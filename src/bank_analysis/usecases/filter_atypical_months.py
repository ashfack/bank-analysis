from typing import List
from ..domain import analysis as domain_analysis
from ..domain.dto import MonthlySummaryRow, FilteredSummaryResult

class FilterAtypicalMonthsUseCase:
    def execute(self, monthly_summary: List[MonthlySummaryRow]) -> FilteredSummaryResult:
        if not monthly_summary:
            raise ValueError("Monthly summary list is empty.")
        return domain_analysis.filter_atypical_months(monthly_summary)
