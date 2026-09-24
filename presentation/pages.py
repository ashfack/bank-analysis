import streamlit as st

from dashboard import build_pilotage_table, style_pilotage_table
from model.models import BudgetView, EnrichedTransaction
from reporting.projections import build_category_table, build_ledger_table


def render_active_page(
    active_navigation: str,
    view: BudgetView,
    reporting_data: list[EnrichedTransaction],
) -> None:
    if active_navigation == "📑 Pilotage":
        render_pilotage(view)
    elif active_navigation == "🔍 Details Discovery":
        render_details(view)
    elif active_navigation == "📝 Transaction Ledger":
        render_ledger(view, reporting_data)


def render_pilotage(view: BudgetView) -> None:
    st.subheader("Master Cluster Time-Series")
    st.caption(
        "Sélectionnez une cellule de dépense pour ouvrir les opérations correspondantes."
    )
    table = build_pilotage_table(view)
    column_config = {
        "Cycle": st.column_config.TextColumn("Cycle", width="medium"),
        **{
            cluster: st.column_config.NumberColumn(
                cluster, format="%.0f €", width="small"
            )
            for cluster in view.clusters
        },
    }
    event = st.dataframe(
        style_pilotage_table(table, view),
        width="stretch",
        height=720,
        hide_index=True,
        column_config=column_config,
        key="pilotage_table",
        on_select="rerun",
        selection_mode="single-cell",
        placeholder="—",
    )

    if event.selection.cells:
        row_index, cluster = event.selection.cells[0]
        if row_index > 0 and cluster != "Cycle":
            cycle = table.iloc[row_index]["Cycle"]
            if view.get_amount(cycle, cluster) > 0:
                st.session_state["sel_cycle"] = cycle
                st.session_state["sel_cluster"] = cluster
                st.session_state["nav_index"] = 2
                st.rerun()


def render_details(view: BudgetView) -> None:
    st.subheader("AI Strategy Metrics")
    table = build_category_table(view)
    if st.session_state["sel_cluster"] != "All Clusters":
        table = table[table["master_cluster"] == st.session_state["sel_cluster"]]
    st.dataframe(table, width="stretch", hide_index=True)


def render_ledger(
    view: BudgetView,
    reporting_data: list[EnrichedTransaction],
) -> None:
    selected_cycle = st.session_state["sel_cycle"]
    selected_cluster = st.session_state["sel_cluster"]
    st.subheader(f"Ledger: {selected_cycle} | {selected_cluster}")
    table = build_ledger_table(view, reporting_data)

    if selected_cycle != "All Cycles":
        table = table[table["cycle"] == selected_cycle]
    if selected_cluster != "All Clusters":
        table = table[table["master_cluster"] == selected_cluster]

    st.metric("Total", f"{table['amount'].sum():,.2f} €")
    columns = ["cycle", "master_cluster", "category", "label", "amount"]
    st.dataframe(
        table[columns].sort_values("amount", ascending=False),
        width="stretch",
        hide_index=True,
    )
