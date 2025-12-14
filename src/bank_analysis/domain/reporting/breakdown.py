from collections import defaultdict
from typing import Sequence, List

from bank_analysis.domain.entities import Transaction
from bank_analysis.domain.reporting.policies import BudgetPolicy, DEFAULT_POLICY
from bank_analysis.domain.value_objects import CategoryBreakdown


def compute_category_breakdown(
    transactions: Sequence[Transaction],
    policy: BudgetPolicy = DEFAULT_POLICY,
) -> List[CategoryBreakdown]:
  """
  Advanced mode: breakdown by category parent (total + number of operations):
    - filters out parents in exclude_parents
    - considers only expenses (amount < 0)
    - sums absolute values of expenses per category_parent
    - counts operations per category_parent
    - sorts by category_parent

  Returns:
      List[CategoryBreakdown]: sorted by category_parent.
  """
  totals = defaultdict(float)
  counts = defaultdict(int)

  for tx in transactions:
    # Skip if category_parent is missing
    cp = tx.category_parent
    if cp is None:
      continue

    # Filter non-internal (not in excluded list) and negative amounts (expenses)
    if cp not in policy.exclude_parents and tx.amount < 0:
      # Accumulate absolute value (equivalent to pandas .abs() on the sum)
      totals[cp] += -tx.amount
      counts[cp] += 1

  # Build rows sorted by category_parent, and round totals to 2 decimals
  rows = [
    CategoryBreakdown(
        label=cp,
        total=round(totals[cp], 2),
        nb_operations=counts[cp],
    )
    for cp in sorted(totals.keys())
  ]

  return rows
