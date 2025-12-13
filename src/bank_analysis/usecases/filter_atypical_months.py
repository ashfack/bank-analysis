from typing import List
from ..domain.reporting import filtering
from ..domain.value_objects import MonthlySummary, FilteredSummary

class FilterAtypicalMonthsUseCase:
    def execute(self, monthly_summary: List[MonthlySummary]) -> FilteredSummary:
        if not monthly_summary:
            raise ValueError("Monthly summary list is empty.")
        return filtering.filter_atypical_months(monthly_summary)
