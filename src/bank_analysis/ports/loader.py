from abc import ABC, abstractmethod
from typing import List, Sequence
from bank_analysis.domain.entities import Transaction

class DataLoaderPort(ABC):
    """Abstract port for loading transaction data in domain form."""

    @abstractmethod
    def list_csv_files(self) -> List[str]:
        """List CSV files available from the loader's base_path (if applicable)."""
        raise NotImplementedError

    @abstractmethod
    def load_and_prepare(self, source: str) -> Sequence[Transaction]:
        """
        Return normalized transactions with fields:
        date_op (date), month (YYYY-MM), category, category_parent, amount (float).
        """
        raise NotImplementedError
