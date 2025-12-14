
from __future__ import annotations
import csv
import os
import unicodedata
from io import StringIO
from datetime import datetime
from typing import List, Optional, Sequence

from bank_analysis.domain.entities import Transaction
from bank_analysis.ports.loader import DataLoaderPort

def _strip_nbsp(s: Optional[str]) -> str:
    if not isinstance(s, str):
        return "" if s is None else str(s)
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("\xa0", " ").replace("\u202f", " ")
    return s.strip()

def _normalize_header(h: Optional[str]) -> str:
    """Remove BOM, normalize and strip header names."""
    if h is None:
        return ""
    h = unicodedata.normalize("NFKC", h)
    return h.replace("\ufeff", "").replace("\xa0", " ").replace("\u202f", " ").strip()

def parse_amount(value: Optional[str]) -> Optional[float]:
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

class CsvContentDataLoader(DataLoaderPort):
    """CSV adapter tuned to semicolon CSV (comma decimals) — raw string input."""

    def __init__(self, base_path: str = "."):
        self.base_path = base_path

    def list_csv_files(self) -> List[str]:
        return [f for f in os.listdir(self.base_path) if f.lower().endswith(".csv")]

    def load_and_prepare(self, source: str) -> Sequence[Transaction]:
        """
        Read CSV from a raw string and return normalized Transaction objects.
        Handles BOM in header: \ufeffdateOp -> dateOp
        """
        # 1) Strip BOM if present (most common cause of 'ufeffdateOp')
        source = source.lstrip("\ufeff")

        # 2) Build reader and normalize headers
        io = StringIO(source)
        # Peek first row to normalize headers
        header_reader = csv.reader(io, delimiter=";")
        try:
            raw_headers = next(header_reader)
        except StopIteration:
            return []

        headers = [_normalize_header(h) for h in raw_headers]

        # DictReader continues from current position, with normalized headers
        reader = csv.DictReader(io, fieldnames=headers, delimiter=";")

        txns: list[Transaction] = []
        for row in reader:
            # Normalize keys just in case there are stray BOMs or NBSPs
            row = { _normalize_header(k): v for k, v in row.items() }

            date_raw = row.get("dateOp")
            amount_raw = row.get("amount")
            amount = parse_amount(amount_raw)

            if amount is None or not date_raw:
                continue

            try:
                d = datetime.fromisoformat(_strip_nbsp(date_raw)).date()
            except Exception:
                continue

            month = row.get("month") or f"{d.year:04d}-{d.month:02d}"
            category = _strip_nbsp(row.get("category"))
            category_parent = _strip_nbsp(row.get("categoryParent"))
            supplier_found = _strip_nbsp(row.get("supplierFound"))

            txns.append(Transaction(
                date_op=d,
                month=month,
                category=category,
                category_parent=category_parent,
                amount=float(amount),
                supplier=supplier_found
            ))
        return txns
