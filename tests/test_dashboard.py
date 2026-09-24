from dashboard import build_pilotage_table, style_pilotage_table
from model.models import BudgetView, ProcessedCategory


def _view() -> BudgetView:
    return BudgetView(
        matrix={
            "Cycle_du_2026-02-01": {"2. Food": 120.0, "10. Carburant": 0.0},
            "Cycle_du_2026-01-01": {"2. Food": 40.0, "10. Carburant": 80.0},
        },
        cluster_budgets={"2. Food": 100.0, "10. Carburant": 100.0},
        processed_categories=[
            ProcessedCategory("Food", "2. Food", 0, 0, 0, 0, 0, 100, 0),
            ProcessedCategory("Fuel", "10. Carburant", 0, 0, 0, 0, 0, 100, 0),
        ],
    )


def test_pilotage_table_keeps_budget_and_cycles_numeric():
    table = build_pilotage_table(_view())

    assert list(table.columns) == ["Cycle", "10. Carburant", "2. Food"]
    assert table.iloc[0].to_dict() == {
        "Cycle": "BUDGET THÉORIQUE",
        "10. Carburant": 100.0,
        "2. Food": 100.0,
    }
    assert table.iloc[1]["Cycle"] == "Cycle_du_2026-02-01"
    assert table.iloc[1]["2. Food"] == 120.0


def test_pilotage_table_uses_shared_budget_colors():
    table = build_pilotage_table(_view())
    context = style_pilotage_table(table, _view())._compute().ctx

    assert ("background-color", "#FFFFFF") in context[(1, 1)]
    assert ("background-color", "#ED7D31") in context[(1, 2)]
    assert ("background-color", "#50BE5B") in context[(2, 1)]
