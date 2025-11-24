
from typing import Protocol, Sequence
from bank_analysis.domain.entities import Transaction

class TransactionRepository(Protocol):
    def list(self) -> Sequence[Transaction]:
        """Return all transactions."""
