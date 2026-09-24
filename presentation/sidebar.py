from dataclasses import dataclass
from typing import Any

import streamlit as st


NAVIGATION_OPTIONS = [
    "📑 Pilotage",
    "🔍 Details Discovery",
    "📝 Transaction Ledger",
]


@dataclass(frozen=True)
class SidebarInputs:
    active_navigation: str
    bank_export: Any
    mapping_config: Any
    budget_config: Any


def render_sidebar() -> SidebarInputs:
    with st.sidebar:
        st.title("🎯 Control Panel")
        active_navigation = st.radio(
            "Navigation",
            NAVIGATION_OPTIONS,
            index=st.session_state["nav_index"],
        )
        st.session_state["nav_index"] = NAVIGATION_OPTIONS.index(active_navigation)
        st.divider()

        if st.session_state["processed"]:
            _render_focus_filters()

        st.header("📂 Data Ingestion")
        bank_export = st.file_uploader("Operations (CSV)", type=["csv"])
        mapping_config = st.file_uploader("Mapping (CSV)", type=["csv"])
        budget_config = st.file_uploader("Budget (CSV)", type=["csv"])

        if st.button("🗑️ Reset Application"):
            st.session_state.clear()
            st.rerun()

    return SidebarInputs(
        active_navigation=active_navigation,
        bank_export=bank_export,
        mapping_config=mapping_config,
        budget_config=budget_config,
    )


def _render_focus_filters() -> None:
    st.header("Focus Filter")
    view = st.session_state["budget_view"]
    cycles = ["All Cycles", *view.cycles]
    clusters = ["All Clusters", *view.clusters]
    selected_cycle = st.session_state["sel_cycle"]
    selected_cluster = st.session_state["sel_cluster"]
    st.session_state["sel_cycle"] = st.selectbox(
        "Select Cycle:",
        cycles,
        index=cycles.index(selected_cycle) if selected_cycle in cycles else 0,
    )
    st.session_state["sel_cluster"] = st.selectbox(
        "Select Cluster:",
        clusters,
        index=clusters.index(selected_cluster) if selected_cluster in clusters else 0,
    )
