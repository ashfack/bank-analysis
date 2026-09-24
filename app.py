import streamlit as st

from analysis_runner import run_uploaded_analysis
from presentation.pages import render_active_page
from presentation.quality_panel import render_quality_panel
from presentation.session_state import initialize_session_state, store_analysis_result
from presentation.sidebar import render_sidebar


st.set_page_config(
    page_title="AI Financial Orchestrator",
    page_icon="📊",
    layout="wide",
)
initialize_session_state()
sidebar = render_sidebar()

st.title("📊 AI-Powered Financial Orchestrator")

if st.button("🚀 Synchronize & Optimize", width="stretch"):
    uploads = (
        sidebar.bank_export,
        sidebar.mapping_config,
        sidebar.budget_config,
    )
    if all(uploads):
        try:
            with st.spinner("🧠 Orchestrating Domain Logic..."):
                result = run_uploaded_analysis(
                    sidebar.bank_export.getvalue(),
                    sidebar.mapping_config.getvalue(),
                    sidebar.budget_config.getvalue(),
                )
                store_analysis_result(result)
                st.rerun()
        except Exception as error:
            st.error(f"Orchestration Error: {error}")

if st.session_state.get("processed"):
    view = st.session_state["budget_view"]
    quality = st.session_state.get("quality_report")
    if quality:
        render_quality_panel(quality)
    render_active_page(
        sidebar.active_navigation,
        view,
        st.session_state["reporting_data"],
    )

    st.divider()
    st.download_button(
        "📥 Download Excel Report",
        st.session_state["report_bytes"],
        file_name="AI_Budget_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
    )
