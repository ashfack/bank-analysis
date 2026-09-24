from typing import Dict, List

from infrastructure.csv_readers import (
    BudgetCsvReader,
    MappingCsvReader,
    TransactionCsvReader,
)
from model.models import Transaction


class DataLoader:
    """Compatibility facade for file-based entry points."""

    @staticmethod
    def count_duplicate_transactions(path: str) -> int:
        return TransactionCsvReader().count_duplicates(path)

    @staticmethod
    def load_category_cluster_map(path: str) -> Dict[str, str]:
        return MappingCsvReader().read(path)

    @staticmethod
    def load_budget_overrides(path: str) -> Dict[str, str]:
        return BudgetCsvReader().read(path)

    @staticmethod
    def prepare_transaction_data(path: str) -> List[Transaction]:
        return TransactionCsvReader().read(path)
