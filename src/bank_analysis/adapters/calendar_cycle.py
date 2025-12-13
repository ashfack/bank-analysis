from datetime import date
from ..ports.cycle_grouper import CycleGrouper

class CalendarCycleGrouper(CycleGrouper):
    """Group by calendar months using 'YYYY-MM' labels."""
    def label_for_date(self, d: date) -> str:
        return f"{d.year:04d}-{d.month:02d}"
