import pandas as pd
from bank_analysis.domain.analysis import compute_monthly_summary, filter_atypical_months, compute_aggregates

def _build_df(rows):
    return pd.DataFrame(rows)

def test_compute_monthly_summary_basic():
    df = _build_df([
        {"dateOp": "2023-01-05", "amount": 1000.0, "month": "2023-01", "category": "Salaire fixe", "categoryParent": "A"},
        {"dateOp": "2023-01-07", "amount": -200.0, "month": "2023-01", "category": "C", "categoryParent": "B"},
        {"dateOp": "2023-02-01", "amount": -50.0, "month": "2023-02", "category": "C", "categoryParent": "B"},
    ])
    summary = compute_monthly_summary(df)
    assert summary.loc[summary["month"] == "2023-01", "total_savings"].iloc[0] == 800.0
    assert summary.loc[summary["month"] == "2023-02", "total_savings"].iloc[0] == -50.0

def test_filter_atypical_months_and_aggregates():
    df = _build_df([
        {"dateOp": "2023-01-05", "amount": 1000.0, "month": "2023-01", "category": "Salaire fixe", "categoryParent": "A"},
        {"dateOp": "2023-01-07", "amount": -1200.0, "month": "2023-01", "category": "C", "categoryParent": "B"},
        {"dateOp": "2023-02-01", "amount": -50.0, "month": "2023-02", "category": "C", "categoryParent": "B"},
    ])
    summary = compute_monthly_summary(df)
    filtered, excluded = filter_atypical_months(summary)
    assert "2023-01" in excluded
    aggregates = compute_aggregates(filtered)
    assert isinstance(aggregates.mean_savings, float)