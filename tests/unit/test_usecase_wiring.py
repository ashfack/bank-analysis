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

class CapturePresenter(PresenterPort):
    def __init__(self):
        self.last_monthly = None
        self.last_filtered = None
        self.last_aggregates = None
        self.last_breakdown = None

    def present_monthly_summary(self, df):
        self.last_monthly = df

    def present_filtered_summary(self, df, excluded_months):
        self.last_filtered = (df, excluded_months)

    def present_aggregates(self, aggregates: domain_analysis.AggregateMetrics):
        self.last_aggregates = aggregates

    def present_category_breakdown(self, df):
        self.last_breakdown = df

def test_usecase_runs_and_presents():
    df = pd.DataFrame([
        {"dateOp": "2023-01-05", "amount": 1000.0, "month": "2023-01", "category": "Salaire fixe", "categoryParent": "A"},
        {"dateOp": "2023-01-07", "amount": -200.0, "month": "2023-01", "category": "C", "categoryParent": "B"},
    ])
    loader = FakeLoader(df)
    presenter = CapturePresenter()
    uc = AnalyzeBudgetUseCase(loader, presenter)
    out = uc.run_from_path("unused.csv", do_filter_atypical=False, show_category_breakdown=True)
    assert presenter.last_monthly is not None
    assert presenter.last_aggregates is not None
    assert presenter.last_breakdown is not None
    assert out["monthly_summary"].shape[0] >= 1