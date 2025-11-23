from typing import List
import pandas as pd
from bank_analysis.usecases.analyze_budget import AnalyzeBudgetUseCase
from bank_analysis.ports.presenter import PresenterPort
from bank_analysis.ports.loader import DataLoaderPort
from bank_analysis.domain import analysis as domain_analysis

class FakeLoader(DataLoaderPort):
    def __init__(self, df):
        self._df = df
    def list_csv_files(self) -> List[str]:
        return ["dummy.csv"]
    def load_and_prepare(self, csv_path: str) -> pd.DataFrame:
        return self._df

def test_usecase_runs_and_presents():
    df = pd.DataFrame([
        {"dateOp": "2023-01-05", "amount": 1000.0, "month": "2023-01", "category": "Salaire fixe", "categoryParent": "A"},
        {"dateOp": "2023-01-07", "amount": -200.0, "month": "2023-01", "category": "C", "categoryParent": "B"},
    ])
    loader = FakeLoader(df)
    uc = AnalyzeBudgetUseCase(loader)
    out = uc.run_full_analysis("unused.csv", do_filter_atypical=False, show_category_breakdown=True)
    assert len(out["monthly_summary"]) >=1
    assert out["aggregates"] is not None
    assert len(out["category_breakdown"]) >=1
