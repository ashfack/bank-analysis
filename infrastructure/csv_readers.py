from io import BytesIO, StringIO
import os
from pathlib import Path
from typing import BinaryIO, Dict, List, TextIO, Union

import pandas as pd

from config.config import (
    COL_RAW_AMOUNT,
    COL_RAW_CATEGORY,
    COL_RAW_CLUSTER,
    COL_RAW_DATE,
    COL_RAW_OVERRIDE,
    CSV_SEP,
    DOMAIN_DATE,
    ENCODING,
)
from model.models import Transaction


CsvSource = Union[str, Path, bytes, BinaryIO, TextIO]


def _missing_path(source: CsvSource) -> bool:
    return isinstance(source, (str, Path)) and not os.path.exists(source)


def _read_csv(source: CsvSource) -> pd.DataFrame:
    readable_source = BytesIO(source) if isinstance(source, bytes) else source
    return pd.read_csv(readable_source, sep=CSV_SEP, encoding=ENCODING)


def _read_text(source: CsvSource) -> str:
    if isinstance(source, bytes):
        return source.decode(ENCODING)
    if isinstance(source, (str, Path)):
        return Path(source).read_text(encoding=ENCODING)
    content = source.read()
    return content.decode(ENCODING) if isinstance(content, bytes) else content


class TransactionCsvReader:
    def read(self, source: CsvSource) -> List[Transaction]:
        if _missing_path(source):
            raise FileNotFoundError(f"Input data not found at {source}")

        frame = _read_csv(source)
        required = {COL_RAW_DATE, COL_RAW_AMOUNT}
        if not required.issubset(frame.columns):
            missing = required - set(frame.columns)
            raise ValueError(f"File at {source} missing required columns: {missing}")

        frame[COL_RAW_AMOUNT] = (
            frame[COL_RAW_AMOUNT]
            .astype(str)
            .str.replace(r"[\xa0 ]", "", regex=True)
            .str.replace(",", ".")
            .astype(float)
        )
        frame[DOMAIN_DATE] = pd.to_datetime(frame[COL_RAW_DATE])
        transactions = [
            Transaction(
                dateOperation=row[DOMAIN_DATE],
                label=str(row.get("label", "Unknown")),
                amount=row[COL_RAW_AMOUNT],
                category=row[COL_RAW_CATEGORY],
            )
            for _, row in frame.iterrows()
        ]
        return sorted(transactions, key=lambda item: item.dateOperation)

    def count_duplicates(self, source: CsvSource) -> int:
        if _missing_path(source):
            raise FileNotFoundError(f"Input data not found at {source}")
        return int(_read_csv(source).duplicated(keep="first").sum())


class MappingCsvReader:
    def read(self, source: CsvSource) -> Dict[str, str]:
        if _missing_path(source):
            return {}

        frame = _read_csv(source)
        if not {COL_RAW_CATEGORY, COL_RAW_CLUSTER}.issubset(frame.columns):
            return {}

        duplicated_categories = (
            frame.loc[
                frame[COL_RAW_CATEGORY].duplicated(keep=False),
                COL_RAW_CATEGORY,
            ]
            .dropna()
            .astype(str)
            .unique()
        )
        if duplicated_categories.size:
            duplicates = ", ".join(sorted(duplicated_categories))
            raise ValueError(f"Duplicate category mappings: {duplicates}")
        return dict(zip(frame[COL_RAW_CATEGORY], frame[COL_RAW_CLUSTER]))


class BudgetCsvReader:
    def read(self, source: CsvSource) -> Dict[str, str]:
        if _missing_path(source):
            return {}

        rows = [
            line.strip()
            for line in _read_text(source).splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        if not rows:
            return {}

        try:
            frame = pd.read_csv(StringIO("\n".join(rows)), sep=CSV_SEP)
        except Exception:
            return {}

        if not {COL_RAW_CATEGORY, COL_RAW_OVERRIDE}.issubset(frame.columns):
            return {}
        return dict(zip(frame[COL_RAW_CATEGORY], frame[COL_RAW_OVERRIDE]))
