import pandas as pd
from ..ports.loader import DataLoaderPort

class DataLoadingUseCase:
    def __init__(self, loader: DataLoaderPort):
        self.loader = loader

    def execute(self, csv_path: str) -> pd.DataFrame:
        if not csv_path:
            raise ValueError("CSV path cannot be empty.")
        df = self.loader.load_and_prepare(csv_path)
        if df.empty:
            raise ValueError("Loaded DataFrame is empty.")
        return df
