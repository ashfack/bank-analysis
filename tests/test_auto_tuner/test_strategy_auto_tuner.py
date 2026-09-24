import pandas as pd

from auto_tuner.strategy_auto_tuner import StrategyAutoTuner
from config.config import BudgetStrategy
from model.models import BudgetDomain, StrategyConfig, Transaction
from orchestrator import Orchestrator


def _orchestrator(last_expense: float) -> Orchestrator:
    transactions = [
        Transaction(pd.Timestamp("2026-01-01"), "Salary 1", 2000.0, "Salaire fixe"),
        Transaction(pd.Timestamp("2026-01-02"), "Expense 1", -100.0, "Expense"),
        Transaction(pd.Timestamp("2026-02-01"), "Salary 2", 2000.0, "Salaire fixe"),
        Transaction(pd.Timestamp("2026-02-02"), "Expense 2", -120.0, "Expense"),
        Transaction(pd.Timestamp("2026-03-01"), "Salary 3", 2000.0, "Salaire fixe"),
        Transaction(pd.Timestamp("2026-03-02"), "Expense 3", -last_expense, "Expense"),
    ]
    return Orchestrator(BudgetDomain(
        transactions=transactions,
        category_cluster_map={"Salaire fixe": "0. Incoming", "Expense": "2. Expense"},
        budget_overrides={},
    ))


def test_temporal_validation_keeps_latest_cycle_out_of_training():
    training, validation = StrategyAutoTuner._prepare_temporal_validation(_orchestrator(900.0))

    assert {item["cycle"] for item in training.reporting_data} == {
        "Cycle_du_2026-01-01",
        "Cycle_du_2026-02-01",
    }
    assert validation["Expense"] == [("Cycle_du_2026-03-01", 900.0)]


def test_future_amount_does_not_change_fitted_budget():
    low_future, _ = StrategyAutoTuner._prepare_temporal_validation(_orchestrator(10.0))
    high_future, _ = StrategyAutoTuner._prepare_temporal_validation(_orchestrator(10000.0))

    config = StrategyConfig()
    low_budget = low_future.run_pipeline(BudgetStrategy.HYBRID_VOLATILITY, config)
    high_budget = high_future.run_pipeline(BudgetStrategy.HYBRID_VOLATILITY, config)

    assert low_budget == high_budget


def test_short_history_uses_explicit_full_history_fallback():
    transactions = [
        Transaction(pd.Timestamp("2026-01-01"), "Salary", 2000.0, "Salaire fixe"),
        Transaction(pd.Timestamp("2026-01-02"), "Expense", -100.0, "Expense"),
    ]
    orchestrator = Orchestrator(BudgetDomain(transactions, {}, {}))

    training, validation = StrategyAutoTuner._prepare_temporal_validation(orchestrator)

    assert training is orchestrator
    assert validation["Expense"] == [("Cycle_du_2026-01-01", 100.0)]
