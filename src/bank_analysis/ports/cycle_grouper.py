from typing import Protocol
from datetime import date

class CycleGrouper(Protocol):
    def label_for_date(self, d: date) -> str:
        """Return a period label for a given date (e.g., 'YYYY-MM', or 'YYYY-MM-DD to YYYY-MM-DD')."""
