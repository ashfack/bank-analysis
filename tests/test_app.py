from pathlib import Path

from streamlit.testing.v1 import AppTest

from model.models import (
    BudgetView,
    DataQualityReport,
    EnrichedTransaction,
    ProcessedCategory,
)


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def _processed_app() -> AppTest:
    view = BudgetView(
        matrix={"Cycle_du_2026-01-01": {"1. Core": 10.0}},
        cluster_budgets={"1. Core": 100.0},
        processed_categories=[
            ProcessedCategory(
                category="Food",
                master_cluster="1. Core",
                median=10.0,
                std_dev=0.0,
                count=1,
                frequency=1.0,
                base_limit=10.0,
                theoretical_budget=100.0,
                total_actual_spending=10.0,
            )
        ],
    )
    app = AppTest.from_file(APP_PATH)
    app.session_state["processed"] = True
    app.session_state["sel_cycle"] = "All Cycles"
    app.session_state["sel_cluster"] = "All Clusters"
    app.session_state["nav_index"] = 0
    app.session_state["budget_view"] = view
    app.session_state["reporting_data"] = [
        EnrichedTransaction(
            category="Food",
            amount=10.0,
            raw_amount=-10.0,
            label="Market",
            cycle="Cycle_du_2026-01-01",
        )
    ]
    app.session_state["report_bytes"] = b"synthetic workbook"
    app.session_state["quality_report"] = DataQualityReport(
        duplicate_transaction_count=2,
        auto_classified_categories=("Food",),
        unused_budget_targets=("Unused cluster",),
    )
    return app


def test_processed_app_renders_compact_quality_summary_and_pilotage():
    app = _processed_app().run(timeout=20)

    assert not app.exception
    assert [item.label for item in app.expander] == [
        "⚠️ Qualité des données — 3 point(s) à vérifier"
    ]
    assert len(app.warning) == 3
    assert "2 ligne(s) d'opération" in app.warning[0].value
    assert "1 catégorie(s) sans mapping manuel" in app.warning[1].value
    assert "1 entrée(s) de budget" in app.warning[2].value
    assert app.subheader[0].value == "Master Cluster Time-Series"
    assert len(app.dataframe) == 1


def test_processed_app_can_open_the_transaction_ledger():
    app = _processed_app().run(timeout=20)

    app.radio[0].set_value("📝 Transaction Ledger").run(timeout=20)

    assert not app.exception
    assert app.subheader[0].value == "Ledger: All Cycles | All Clusters"
    assert app.metric[0].value == "10.00 €"
    assert len(app.dataframe) == 1
