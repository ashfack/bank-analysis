from io import StringIO
import os
import unicodedata
import pandas as pd
from typing import List, Optional
from ..ports.loader import DataLoaderPort

def _strip_nbsp(s: Optional[str]) -> str:
    """Remove non-breaking spaces and normalize string."""
    if not isinstance(s, str):
        return "" if s is None else str(s)
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("\xa0", " ").replace("\u202f", " ")
    return s.strip()

def parse_amount(value):
    """Convert value to float, handle commas as decimals and quotes."""
    if pd.isna(value):
        return pd.NA
    s = _strip_nbsp(value)
    if s == "":
        return pd.NA
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        s = s[1:-1]
    s = s.replace(" ", "").replace("\u202f", "").replace("\xa0", "")
    s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        s = s.replace('"', '')
        try:
            return float(s)
        except Exception:
            return pd.NA

class CsvFileDataLoader(DataLoaderPort):
    """CSV adapter tuned to demo.csv (semicolon sep, comma decimals)."""

    def __init__(self, base_path: str = "."):
        self.base_path = base_path

    def list_csv_files(self) -> List[str]:
        files = [f for f in os.listdir(self.base_path) if f.lower().endswith('.csv')]
        return files
    

    def read_csv_content(self, source: str) -> pd.DataFrame:
        """
        Reads CSV content from either a file path or a raw string.
        """
        return pd.read_csv(source, sep=";", dtype=str, encoding="utf-8", keep_default_na=False)

    def prepare_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Parses and enriches the DataFrame with date, amount, month, and category columns.
        """
        # dateOp -> datetime
        if "dateOp" in df.columns:
            df["dateOp"] = pd.to_datetime(df["dateOp"], errors="coerce", format="%Y-%m-%d")
        else:
            df["dateOp"] = pd.NaT

        # parse amounts robustly
        if "amount" in df.columns:
            df["amount"] = df["amount"].apply(parse_amount).astype("Float64")
        else:
            df["amount"] = pd.NA

        # month from dateOp
        df["month"] = df["dateOp"].dt.to_period("M").astype(str)

        # ensure category columns exist
        if "category" not in df.columns:
            df["category"] = ""
        if "categoryParent" not in df.columns:
            df["categoryParent"] = ""

        return df



    def load_and_prepare(self, source: str) -> pd.DataFrame:    
        """
        Combines reading and preparing steps.
        """
        df = self.read_csv_content(source)
        return self.prepare_dataframe(df)
        