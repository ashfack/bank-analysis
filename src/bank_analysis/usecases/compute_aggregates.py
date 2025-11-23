from typing import List
from ..domain import analysis as domain_analysis
from ..domain.dto import MonthlySummaryRow, AggregateMetrics

class ComputeAggregatesUseCase:
    def execute(self, summary: List[MonthlySummaryRow]) -> AggregateMetrics:
        if summary is None:
            raise ValueError("Summary cannot be None.")
        return domain_analysis.compute_aggregates(summary)
