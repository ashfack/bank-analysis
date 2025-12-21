from typing import List

from ..domain.entities import Transaction
from ..domain.reporting import filtering
from ..domain.value_objects import BreakdownKind


class FilterTransactionsUseCase:
    def execute(self,
        transactions: List[Transaction],
    period: str,
    label: str,
    kind: BreakdownKind) -> list[Transaction]:
        if not transactions:
            raise ValueError(" no transactions provided")
        return filtering.filter_transactions_by_period_label_and_kind(transactions, period, label, kind)
