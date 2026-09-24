import pandas as pd

from domain.cycle_assigner import CycleAssigner
from model.models import Transaction


def test_assigns_initial_and_latest_preceding_anchor_cycles():
    transactions = [
        Transaction(pd.Timestamp("2026-01-01"), "Before", -10, "Expense"),
        Transaction(pd.Timestamp("2026-01-05"), "Income", 2000, "Salary"),
        Transaction(pd.Timestamp("2026-01-06"), "After first", -20, "Expense"),
        Transaction(pd.Timestamp("2026-02-05"), "Income", 2000, "Salary"),
        Transaction(pd.Timestamp("2026-02-08"), "After second", -30, "Expense"),
    ]

    enriched = CycleAssigner("Salary").assign(transactions)

    assert [item.cycle for item in enriched] == [
        "Initial",
        "Cycle_du_2026-01-05",
        "Cycle_du_2026-01-05",
        "Cycle_du_2026-02-05",
        "Cycle_du_2026-02-05",
    ]
    assert enriched[-1].amount == 30
    assert enriched[-1].raw_amount == -30


def test_assigns_everything_to_initial_without_anchor_transactions():
    transactions = [
        Transaction(pd.Timestamp("2026-01-01"), "Purchase", -10, "Expense")
    ]

    enriched = CycleAssigner("Salary").assign(transactions)

    assert enriched[0].cycle == "Initial"
