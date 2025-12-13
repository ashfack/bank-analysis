from typing import List, Sequence
from ..domain import analysis as domain_analysis
from ..domain.dto import CategoryBreakdownRow
from ..domain.entities import Transaction


class ComputeCategoryBreakdownUseCase:
    def __init__(self, exclude_parents: set = domain_analysis.EXCLUDE_EXPENSE_PARENTS):
        self.exclude_parents = exclude_parents

    def execute(self, transactions: Sequence[Transaction]) -> List[CategoryBreakdownRow]:
        if transactions is None or len(transactions) == 0:
            raise ValueError("transactions is None or empty. Cannot compute category breakdown.")
        return domain_analysis.compute_category_breakdown(transactions, self.exclude_parents)
