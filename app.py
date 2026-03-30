import streamlit as st
import os
import pandas as pd
from config.config import BUDGET_FILE, INPUT_FILE, MAPPING_FILE, OUTPUT_FILE
from loader.data_loader import DataLoader
from model.models import BudgetDomain
from orchestrator import Orchestrator
from auto_tuner.strategy_auto_tuner import StrategyAutoTuner
from report_generator.excel_architect import ExcelArchitect


def get_budget_color(val: float, limit: float, cluster: str) -> str:
    """Returns a HEX color string based on budget performance."""
    if "0." in cluster or val == 0:
        return "#548235" if val > 0 else "#FFFFFF"  # Dark Green or White
    if val <= limit:
        return "#50BE5B" if val > limit * 0.5 else "#548235"  # Light vs Dark Green
    if val <= limit * 1.5:
        return "#ED7D31"  # Orange
    return "#C00000"  # Red

def get_text_color(hex_color: str) -> str:
    """Returns white text for dark backgrounds, black for light."""
    return "white" if hex_color != "#FFFFFF" else "black"

# 1. Page Configuration
st.set_page_config(page_title="AI Financial Orchestrator", page_icon="📊", layout="wide")

# Initialize Session State for persistence across reruns
if 'processed' not in st.session_state:
    st.session_state['processed'] = False
if 'sel_cycle' not in st.session_state:
    st.session_state['sel_cycle'] = "All Cycles"
if 'sel_cluster' not in st.session_state:
    st.session_state['sel_cluster'] = "All Clusters"
if 'active_tab' not in st.session_state:
    st.session_state['active_tab'] = 0

# 2. Sidebar: Navigation & Controls
with st.sidebar:
    st.title("🎯 Control Panel")
    
    if st.session_state['processed']:
        st.header("Focus Filter")
        view = st.session_state['budget_view']
        
        # Sync Sidebar with the Domain View Model (The Contract)
        cycles_list = ["All Cycles"] + view.cycles
        clusters_list = ["All Clusters"] + view.clusters
        
        st.session_state['sel_cycle'] = st.selectbox(
            "Select Cycle (Period):", 
            cycles_list, 
            index=cycles_list.index(st.session_state['sel_cycle']) if st.session_state['sel_cycle'] in cycles_list else 0
        )
        st.session_state['sel_cluster'] = st.selectbox(
            "Select Cluster:", 
            clusters_list, 
            index=clusters_list.index(st.session_state['sel_cluster']) if st.session_state['sel_cluster'] in clusters_list else 0
        )
        st.divider()

    st.header("📂 Data Ingestion")
    bank_export = st.file_uploader("Operations (CSV)", type=['csv'])
    mapping_cfg = st.file_uploader("Mapping (CSV)", type=['csv'])
    budget_cfg = st.file_uploader("Budget (CSV)", type=['csv'])
    
    if st.button("🗑️ Reset Application"):
        st.session_state.clear()
        st.rerun()

st.title("📊 AI-Powered Financial Orchestrator")

# 3. Execution Engine
if st.button("🚀 Synchronize & Optimize", use_container_width=True):
    if bank_export and mapping_cfg and budget_cfg:
        try:
            # Physical File Sync (Infrastructure)
            os.makedirs(os.path.dirname(INPUT_FILE), exist_ok=True)
            for path, file in {INPUT_FILE: bank_export, MAPPING_FILE: mapping_cfg, BUDGET_FILE: budget_cfg}.items():
                with open(path, "wb") as f: f.write(file.getbuffer())

            with st.spinner("🧠 Orchestrating Domain Logic..."):
                # Load Domain Data via Port
                transactions = DataLoader.prepare_transaction_data(INPUT_FILE)
                mapping = DataLoader.load_category_cluster_map(MAPPING_FILE)
                overrides = DataLoader.load_budget_overrides(BUDGET_FILE)
                domain_data = BudgetDomain(transactions, mapping, overrides)
                
                # Execute Orchestrator (Domain Logic)
                orch = Orchestrator(domain_data)
                best_strat, best_params = StrategyAutoTuner.discover(orch)
                
                view = orch.run_analytics(best_strat, best_params)
                architect = ExcelArchitect(OUTPUT_FILE)
                architect.generate(view, orch.reporting_data)
                st.session_state['budget_view'] = view
                st.session_state['raw_data'] = pd.DataFrame(orch.reporting_data) # For Ledger detail
                st.session_state['processed'] = True
                st.rerun()
        except Exception as e:
            st.error(f"Orchestration Error: {e}")

# 4. Interactive Dashboard (The Adapter)
if st.session_state.get('processed'):
    view = st.session_state['budget_view']
    
    # Navigation Tabs
    tabs = st.tabs(["📑 Pilotage", "🔍 Details", "📝 Ledger"])

    # --- TAB 1: PILOTAGE (Clickable Matrix) ---
    with tabs[0]:
        st.subheader("Master Cluster Time-Series")
        st.caption("Click any cell to drill down into specific transactions in the Ledger.")
        
        clusters = view.clusters
        cycles = view.cycles

        # Header Row (Clusters)
        header_cols = st.columns([1.5] + [1] * len(clusters))
        header_cols[0].write("**Cycle**")
        for i, cluster in enumerate(clusters):
            header_cols[i+1].markdown(f"<div style='text-align: center'><b>{cluster}</b></div>", unsafe_allow_html=True)

        # Budget Row (Overrides Applied)
        budget_cols = st.columns([1.5] + [1] * len(clusters))
        budget_cols[0].markdown("*:blue[BUDGET THEORIQUE]*")
        for i, cluster in enumerate(clusters):
            budget_val = view.get_budget(cluster)
            budget_cols[i+1].markdown(f"<div style='text-align: center; color: #1E90FF;'><b>{budget_val:,.0f} €</b></div>", unsafe_allow_html=True)
        
        st.divider()

        # Data Rows (Cycles)
        for cycle in cycles:
            row_cols = st.columns([1.5] + [1] * len(clusters))
            row_cols[0].write(f"**{cycle}**")
            
            for i, cluster in enumerate(clusters):
                val = view.get_amount(cycle, cluster)
                limit = view.get_budget(cluster)
                
                # Calculate colors based on your logic
                bg_color = get_budget_color(val, limit, cluster)
                txt_color = get_text_color(bg_color)
                
                # Create a styled container for the button
                # This wraps the button in a colored div to mimic the Excel cell
                with row_cols[i+1]:
                    st.markdown(
                        f"""
                        <div style="
                            background-color: {bg_color}; 
                            padding: 5px; 
                            border-radius: 5px; 
                            text-align: center;
                            border: 1px solid #ddd;
                        ">
                        """, 
                        unsafe_allow_html=True
                    )
                    
                    btn_label = f"{val:,.0f} €" if val > 0 else "—"
                    if st.button(btn_label, key=f"btn_{cycle}_{cluster}", use_container_width=True):
                        st.session_state['sel_cycle'] = cycle
                        st.session_state['sel_cluster'] = cluster
                        st.toast(f"Filtered for {cluster} in {cycle}. Switch to Ledger!")
                    
                    st.markdown("</div>", unsafe_allow_html=True)

    # --- TAB 2: DETAILS (AI Strategy Metrics) ---
    with tabs[1]:
        st.subheader("AI Discovery Statistics")
        # Pure Domain DTOs converted to displayable DF
        stats_df = pd.DataFrame([vars(c) for c in view.processed_categories])
        
        if st.session_state['sel_cluster'] != "All Clusters":
            stats_df = stats_df[stats_df['master_cluster'] == st.session_state['sel_cluster']]
            
        st.dataframe(stats_df, use_container_width=True, hide_index=True)

    # --- TAB 3: LEDGER (Transaction Detail) ---
    with tabs[2]:
        st.subheader(f"Ledger: {st.session_state['sel_cycle']} | {st.session_state['sel_cluster']}")
        
        # Merge AI clusters with raw reporting data for the detailed view
        raw_df = st.session_state['raw_data'].copy()
        ai_map = pd.DataFrame([{'category': c.category, 'master_cluster': c.master_cluster} 
                               for c in view.processed_categories])
        ledger_df = raw_df.merge(ai_map, on='category', how='left')

        # Apply Current Filters
        if st.session_state['sel_cycle'] != "All Cycles":
            ledger_df = ledger_df[ledger_df['cycle'] == st.session_state['sel_cycle']]
        if st.session_state['sel_cluster'] != "All Clusters":
            ledger_df = ledger_df[ledger_df['master_cluster'] == st.session_state['sel_cluster']]

        # Summary Metric
        current_sum = ledger_df['amount'].sum()
        st.metric("Total in View", f"{current_sum:,.2f} €")

        st.dataframe(
            ledger_df[['cycle', 'master_cluster', 'category', 'label', 'amount']].sort_values('amount', ascending=False),
            use_container_width=True,
            hide_index=True
        )

# 5. Global Export
if st.session_state.get('processed'):
    st.divider()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "rb") as f:
            st.download_button("📥 Download Final Analysis (Excel)", f, file_name="AI_Budget_Report.xlsx", use_container_width=True)