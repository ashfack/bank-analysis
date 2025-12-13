from typing import List

from ..domain.reporting  import aggregates
from ..domain.value_objects import MonthlySummary, AggregateMetrics

class ComputeAggregatesUseCase:
    def execute(self, summary: List[MonthlySummary]) -> AggregateMetrics:
        if summary is None:
            raise ValueError("Summary cannot be None.")
        return aggregates.compute_aggregates(summary)
