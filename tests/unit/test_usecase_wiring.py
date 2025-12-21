from datetime import date
from typing import List, Sequence

from bank_analysis.adapters.calendar_cycle import CalendarCycleGrouper
from bank_analysis.domain.entities import Transaction
from bank_analysis.usecases.full_global_analysis import FullGlobalAnalysisUseCase
from bank_analysis.ports.loader import DataLoaderPort

class FakeLoader(DataLoaderPort):
    def __init__(self, transactions: List[Transaction]):
        self._transactions = transactions
    def list_csv_files(self) -> List[str]:
        return ["dummy.csv"]
    def load_and_prepare(self, csv_path: str) -> Sequence[Transaction]:
        return self._transactions

def test_usecase_runs_and_presents():
    df =[
      Transaction(date_op=date(2025,2,10), month="2025-02", category="Dinner",    category_parent="Leisure",    amount=-65.0, message="DINNER MCDO"),
      Transaction(date_op=date(2025,3,10), month="2025-04", category="Fool",    category_parent="Hobby",    amount=-65.0, message="Ravinder")
         ]
    loader = FakeLoader(df)
    cycle_grouper = CalendarCycleGrouper()
    uc = FullGlobalAnalysisUseCase(loader, cycle_grouper)
    out = uc.run_full_analysis("unused.csv", do_filter_atypical=False, show_category_breakdown=False)
    assert len(out["monthly_summary"]) >=1
    assert out["aggregates"] is not None
    assert out["category_breakdown"] is None
