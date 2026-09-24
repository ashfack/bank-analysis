from model.models import BudgetView, EnrichedTransaction, ProcessedCategory
from reporting.projections import build_category_table, build_ledger_table


def _view() -> BudgetView:
    return BudgetView(
        matrix={},
        cluster_budgets={"2. Food": 100.0},
        processed_categories=[
            ProcessedCategory("Food", "2. Food", 10, 0, 1, 1, 10, 100, 10)
        ],
    )


def test_category_table_projects_processed_categories():
    table = build_category_table(_view())

    assert table.loc[0, "category"] == "Food"
    assert table.loc[0, "master_cluster"] == "2. Food"


def test_ledger_table_attaches_resolved_clusters():
    transactions = [
        EnrichedTransaction("Food", 10, -10, "Market", "Cycle_du_2026-01-01")
    ]

    table = build_ledger_table(_view(), transactions)

    assert table.loc[0, "master_cluster"] == "2. Food"
    assert table.loc[0, "raw_amount"] == -10
