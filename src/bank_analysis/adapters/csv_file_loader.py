from __future__ import annotations

import csv
import os
import unicodedata
from datetime import datetime
from io import StringIO
from typing import List, Optional, Sequence

from bank_analysis.domain.entities import Transaction
from bank_analysis.ports.loader import DataLoaderPort


# ---------- Utils ----------

def _strip_nbsp(s: Optional[str]) -> str:
    """Normalize in NFKC, suppress NBSP et other spaces, puis strip."""
    if not isinstance(s, str):
        return "" if s is None else str(s)
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("\xa0", " ").replace("\u202f", " ")
    return s.strip()


def _normalize_header(h: Optional[str]) -> str:
    """Normalize header (BOM, NBSP, spaces, strip)."""
    if h is None:
        return ""
    h = unicodedata.normalize("NFKC", h)
    return h.replace("\ufeff", "").replace("\xa0", " ").replace("\u202f", " ").strip()


def parse_amount(value: Optional[str]) -> Optional[float]:
    """
    Converts a String to float :
    - handles coma separator for numbers and replacing them with dots,
    - Strip quotes,
    - NBSP and spaces (different kinds),
    Returns None if empty or non parseable.
    """
    if value is None:
        return None

    s = _strip_nbsp(value)
    if s == "":
        return None

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
            return None


def _detect_delimiter(header_line: str) -> str:
    """
    Returns ';' if no separator found.
    """
    semi = header_line.count(";")
    comma = header_line.count(",")
    if semi == 0 and comma == 0:
        return ";"
    return ";" if semi >= comma else ","


# ---------- Adapter ----------

class CsvFileDataLoader(DataLoaderPort):
    """
    - Supported separators: ';' et ',' (auto-detection with first line).
    - Encoding: 'utf-8-sig' (workaround for BOM).
    - Minimal expected columns (min): 'dateOp', 'amount'.
    - Optional columns: 'month', 'category', 'categoryParent'.
    """

    def __init__(self, base_path: str = "."):
        self.base_path = base_path

    def list_csv_files(self) -> List[str]:
        return [f for f in os.listdir(self.base_path) if f.lower().endswith(".csv")]

    def load_and_prepare(self, source: str) -> Sequence[Transaction]:
        txns: list[Transaction] = []

        with open(source, encoding="utf-8-sig") as f:
            text = f.read()

        if not text.strip():
            return []

        lines = text.splitlines()
        raw_header = lines[0]
        delim = _detect_delimiter(raw_header)


        raw_headers = raw_header.split(delim)
        headers = [_normalize_header(h) for h in raw_headers]

        if not {"dateOp", "amount"}.issubset(set(headers)):
            # Invalid header
            return []

        normalized_text = delim.join(headers) + "\n" + "\n".join(lines[1:])
        io = StringIO(normalized_text)

        reader = csv.DictReader(io, delimiter=delim)
        for row in reader:
            # Safety normalization
            row = {_normalize_header(k): v for k, v in row.items()}

            date_raw = _strip_nbsp(row.get("dateOp"))
            amount_raw = _strip_nbsp(row.get("amount"))

            if not date_raw:
                continue

            amount = parse_amount(amount_raw)
            if amount is None:
                continue

            # Date ISO 'YYYY-MM-DD'
            try:
                d = datetime.fromisoformat(date_raw).date()
            except Exception:
                cleaned = date_raw.replace('"', '').strip()
                try:
                    d = datetime.fromisoformat(cleaned).date()
                except Exception:
                    continue

            # Optional fields
            month = _strip_nbsp(row.get("month")) or f"{d.year:04d}-{d.month:02d}"
            category = _strip_nbsp(row.get("category"))
            category_parent = _strip_nbsp(row.get("categoryParent"))

            txns.append(Transaction(
                date_op=d,
                month=month,
                category=category,
                category_parent=category_parent,
                amount=float(amount),
            ))

        return txns
