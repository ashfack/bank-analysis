from typing import List

from bank_analysis.domain import period_splicer
from bank_analysis.domain.entities import Transaction
from bank_analysis.domain.matcher import _match_supplier
from bank_analysis.domain.reporting.category_rules import DEFAULT_CATEGORY_RULES
from bank_analysis.domain.value_objects import MonthlySummary, FilteredSummary, \
  BreakdownKind


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


def filter_transactions_by_period_label_and_kind(
    transactions: List[Transaction],
    period: str,
    label: str,
    kind: BreakdownKind) \
    -> List[Transaction]:

  period_txs = period_splicer.filter_transactions_by_period(transactions, period)
  if kind == BreakdownKind.SUPPLIER:
    return [t for t in period_txs if _match_supplier(getattr(t, "supplier", None), DEFAULT_CATEGORY_RULES.supplier_patterns)]
  return [t for t in period_txs if t.category.casefold() == label.casefold()]

