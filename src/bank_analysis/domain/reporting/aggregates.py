from typing import List
from ..value_objects import MonthlySummary, AggregateMetrics

def compute_aggregates(summary: List[MonthlySummary]) -> AggregateMetrics:
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