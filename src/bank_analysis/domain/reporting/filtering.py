from typing import List

from bank_analysis.domain.value_objects import MonthlySummary, FilteredSummary


def filter_atypical_months(
    summary: List[MonthlySummary]
) -> FilteredSummary:
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
  return FilteredSummary(filtered=filtered, excluded_months=excluded_months)
