import streamlit as st

from analysis_runner import AnalysisResult


def initialize_session_state() -> None:
    defaults = {
        "processed": False,
        "sel_cycle": "All Cycles",
        "sel_cluster": "All Clusters",
        "nav_index": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def store_analysis_result(result: AnalysisResult) -> None:
    st.session_state["budget_view"] = result.view
    st.session_state["reporting_data"] = result.reporting_data
    st.session_state["report_bytes"] = result.report_bytes
    st.session_state["quality_report"] = result.quality
    st.session_state["processed"] = True
