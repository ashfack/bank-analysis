
from datetime import date, datetime
from typing import Sequence
from bank_analysis.domain.entities import Transaction

def _parse_iso_date(s: str) -> date:
    """Parse an ISO date 'YYYY-MM-DD' to datetime.date (no pandas)."""
    # strip any accidental quotes/whitespaces
    s = s.strip().strip('"').strip("'")
    return datetime.fromisoformat(s).date()

def filter_transactions_by_period(
    txns: Sequence[Transaction],
    period: str,
) -> list[Transaction]:
    """
    Period formats supported:
    - Salary cycle label: 'YYYY-MM-DD to YYYY-MM-DD'  (inclusive bounds)
    - Calendar month: 'YYYY-MM'

    Returns the transactions whose date/month falls within the period.
    """
    period = period.strip()

    # Salary cycle style: 'YYYY-MM-DD to YYYY-MM-DD'
    if " to " in period:
        start_str, end_str = period.split(" to ", 1)
        start_date = _parse_iso_date(start_str)
        end_date = _parse_iso_date(end_str)

        return [
            t for t in txns
            if start_date <= t.date_op <= end_date
        ]

    # Calendar month style: 'YYYY-MM'
    # We rely on your Transaction.month field (already 'YYYY-MM')
    return [t for t in txns if t.month == period]
