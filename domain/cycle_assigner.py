from bisect import bisect_right
from typing import Sequence

from model.models import EnrichedTransaction, Transaction


class CycleAssigner:
    """Assign transactions to the latest preceding anchor transaction."""

    def __init__(self, anchor_category: str):
        self.anchor_category = anchor_category

    def assign(
        self,
        transactions: Sequence[Transaction],
    ) -> list[EnrichedTransaction]:
        anchor_dates = sorted(
            {
                transaction.dateOperation
                for transaction in transactions
                if transaction.category == self.anchor_category
            }
        )

        enriched = []
        for transaction in transactions:
            anchor_index = bisect_right(anchor_dates, transaction.dateOperation) - 1
            cycle = (
                f"Cycle_du_{anchor_dates[anchor_index].strftime('%Y-%m-%d')}"
                if anchor_index >= 0
                else "Initial"
            )
            enriched.append(
                EnrichedTransaction(
                    category=transaction.category,
                    amount=abs(transaction.amount),
                    raw_amount=transaction.amount,
                    label=transaction.label,
                    cycle=cycle,
                )
            )
        return enriched
