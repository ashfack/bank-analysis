from datetime import date, timedelta
from typing import Sequence
from bank_analysis.domain.entities import Transaction
from bank_analysis.ports.cycle_grouper import CycleGrouper

class SalaryCycleGrouper(CycleGrouper):
    """
    Build periods from actual salary dates:
    - Each period starts on a salary date and ends the day before the next salary date.
    - The last period ends at the max date in the dataset.
    - ISO labels: 'YYYY-MM-DD to YYYY-MM-DD' for lexical == chronological sorting.
    """

    def __init__(self, txns: Sequence[Transaction], salary_category: str = "Salaire fixe") -> None:
        # Collect unique salary dates
        salary_dates = sorted({t.date_op for t in txns if t.category == salary_category})
        self._periods: list[tuple[date, date]] = []
        if salary_dates:
            max_date = max(t.date_op for t in txns)
            for i in range(len(salary_dates) - 1):
                start = salary_dates[i]
                end = salary_dates[i + 1] - timedelta(days=1)
                self._periods.append((start, end))
            self._periods.append((salary_dates[-1], max_date))

    def label_for_date(self, d: date) -> str:
        for start, end in self._periods:
            if start <= d <= end:
                return f"{start.isoformat()} to {end.isoformat()}"
        return "Outside salary periods"
