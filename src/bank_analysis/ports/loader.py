from abc import ABC, abstractmethod
from typing import List
import pandas as pd

class DataLoaderPort(ABC):
    """Abstract port for loading transaction data as a DataFrame."""

    @abstractmethod
    def list_csv_files(self) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def load_and_prepare(self, source: str, is_path: bool = True) -> pd.DataFrame:
        """Return a prepared DataFrame matching domain expectations (dateOp, amount, month, category, categoryParent)."""
        raise NotImplementedError