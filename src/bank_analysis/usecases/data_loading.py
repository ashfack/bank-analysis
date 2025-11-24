from typing import Sequence

import pandas as pd

from ..domain.entities import Transaction
from ..ports.loader import DataLoaderPort

class DataLoadingUseCase:
    def __init__(self, loader: DataLoaderPort):
        self.loader = loader

    def execute(self, csv_path: str) -> Sequence[Transaction]:
        if not csv_path:
            raise ValueError("CSV path cannot be empty.")
        transactions = self.loader.load_and_prepare(csv_path)
        if len(transactions) == 0:
            raise ValueError("Loaded content is empty.")
        return transactions
