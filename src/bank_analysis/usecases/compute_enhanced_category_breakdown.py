from typing import List, Sequence
from ..domain.reporting import enhanced_breakdown
from ..domain.value_objects import CategoryBreakdown
from ..domain.entities import Transaction


class ComputeEnhancedCategoryBreakdownUseCase:
    def __init__(self):
      pass

    def execute(self, transactions: Sequence[Transaction]) -> List[CategoryBreakdown]:
        if transactions is None or len(transactions) == 0:
            raise ValueError("transactions is None or empty. Cannot compute category breakdown.")
        return enhanced_breakdown.compute_category_breakdown(transactions)
