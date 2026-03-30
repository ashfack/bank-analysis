import streamlit as st
import os
import pandas as pd
from config.config import BUDGET_FILE, INPUT_FILE, MAPPING_FILE, OUTPUT_FILE
from loader.data_loader import DataLoader
from model.models import BudgetDomain
from orchestrator import Orchestrator
from auto_tuner.strategy_auto_tuner import StrategyAutoTuner
from report_generator.excel_architect import ExcelArchitect

# --- 1. SHARED STYLING LOGIC (Synced with ExcelArchitect) ---
def get_budget_color(val: float, limit: float, cluster: str) -> str:
    if "0." in cluster or val == 0:
        return "#548235" if val > 0 else "#FFFFFF"  
    if val <= limit:
        return "#50BE5B" if val > limit * 0.5 else "#548235"  
    if val <= limit * 1.5:
        return "#ED7D31"  
    return "#C00000"  

def get_text_color(hex_color: str) -> str:
    return "white" if hex_color != "#FFFFFF" else "black"

# --- 2. PAGE CONFIGURATION ---
st.set_page_config(page_title="AI Financial Orchestrator", page_icon="📊", layout="wide")

# Initialize Session State
if 'processed' not in st.session_state:
    st.session_state['processed'] = False
if 'sel_cycle' not in st.session_state:
    st.session_state['sel_cycle'] = "All Cycles"
if 'sel_cluster' not in st.session_state:
    st.session_state['sel_cluster'] = "All Clusters"
if 'nav_index' not in st.session_state:
    st.session_state['nav_index'] = 0  # 0: Pilotage, 1: Details, 2: Ledger

# --- 3. SIDEBAR: NAVIGATION & CONTROLS ---
with st.sidebar:
    st.title("🎯 Control Panel")
    
    # NAVIGATION: Using index from session_state allows the buttons to "force" a page change
    nav_options = ["📑 Pilotage", "🔍 Details Discovery", "📝 Transaction Ledger"]
    active_nav = st.radio(
        "Navigation", 
        nav_options, 
        index=st.session_state['nav_index']
    )
    
    # Update state if the user clicks the radio manually
    st.session_state['nav_index'] = nav_options.index(active_nav)

    st.divider()

    if st.session_state['processed']:
        st.header("Focus Filter")
        view = st.session_state['budget_view']
        
        cycles_list = ["All Cycles"] + view.cycles
        clusters_list = ["All Clusters"] + view.clusters
        
        st.session_state['sel_cycle'] = st.selectbox(
            "Select Cycle:", 
            cycles_list, 
            index=cycles_list.index(st.session_state['sel_cycle']) if st.session_state['sel_cycle'] in cycles_list else 0
        )
        st.session_state['sel_cluster'] = st.selectbox(
            "Select Cluster:", 
            clusters_list, 
            index=clusters_list.index(st.session_state['sel_cluster']) if st.session_state['sel_cluster'] in clusters_list else 0
        )

    st.header("📂 Data Ingestion")
    bank_export = st.file_uploader("Operations (CSV)", type=['csv'])
    mapping_cfg = st.file_uploader("Mapping (CSV)", type=['csv'])
    budget_cfg = st.file_uploader("Budget (CSV)", type=['csv'])
    
    if st.button("🗑️ Reset Application"):
        st.session_state.clear()
        st.rerun()

st.title("📊 AI-Powered Financial Orchestrator")

# --- 4. EXECUTION ENGINE ---
if st.button("🚀 Synchronize & Optimize", use_container_width=True):
    if bank_export and mapping_cfg and budget_cfg:
        try:
            os.makedirs(os.path.dirname(INPUT_FILE), exist_ok=True)
            for path, file in {INPUT_FILE: bank_export, MAPPING_FILE: mapping_cfg, BUDGET_FILE: budget_cfg}.items():
                with open(path, "wb") as f: f.write(file.getbuffer())

            with st.spinner("🧠 Orchestrating Domain Logic..."):
                transactions = DataLoader.prepare_transaction_data(INPUT_FILE)
                mapping = DataLoader.load_category_cluster_map(MAPPING_FILE)
                overrides = DataLoader.load_budget_overrides(BUDGET_FILE)
                domain_data = BudgetDomain(transactions, mapping, overrides)
                
                orch = Orchestrator(domain_data)
                best_strat, best_params = StrategyAutoTuner.discover(orch)
                
                view = orch.run_analytics(best_strat, best_params)
                
                # Excel Architect initialization (Fixed to 1 arg)
                architect = ExcelArchitect(OUTPUT_FILE)
                architect.generate(view, orch.reporting_data)
                
                st.session_state['budget_view'] = view
                st.session_state['raw_data'] = pd.DataFrame(orch.reporting_data)
                st.session_state['processed'] = True
                st.rerun()
        except Exception as e:
            st.error(f"Orchestration Error: {e}")

# --- 5. DASHBOARD VIEW ADAPTER ---
if st.session_state.get('processed'):
    view = st.session_state['budget_view']
    
    # --- PAGE 1: PILOTAGE ---
    if active_nav == "📑 Pilotage":
        st.subheader("Master Cluster Time-Series")
        
        clusters = view.clusters
        cycles = view.cycles

        # Header
        h_cols = st.columns([1.5] + [1] * len(clusters))
        h_cols[0].write("**Cycle**")
        for idx, cluster in enumerate(clusters):
            h_cols[idx+1].markdown(f"<div style='text-align: center'><b>{cluster}</b></div>", unsafe_allow_html=True)

        # Budget Row
        b_cols = st.columns([1.5] + [1] * len(clusters))
        b_cols[0].markdown("*:blue[BUDGET THEORIQUE]*")
        for idx, cluster in enumerate(clusters):
            val = view.get_budget(cluster)
            b_cols[idx+1].markdown(f"<div style='text-align: center; color: #1E90FF;'><b>{val:,.0f} €</b></div>", unsafe_allow_html=True)
        
        st.divider()

        # Data Rows
        for cycle in cycles:
            r_cols = st.columns([1.5] + [1] * len(clusters))
            r_cols[0].write(f"**{cycle}**")
            
            for idx, cluster in enumerate(clusters):
                val = view.get_amount(cycle, cluster)
                limit = view.get_budget(cluster)
                bg = get_budget_color(val, limit, cluster)
                
                with r_cols[idx+1]:
                    # Using a simplified HTML wrapper that won't capture the click
                    st.markdown(f"""<div style="background-color: {bg}; border-radius: 4px; padding: 2px;">""", unsafe_allow_html=True)
                    
                    label = f"{val:,.0f} €" if val > 0 else "—"
                    # KEY is critical here to keep the buttons distinct
                    if st.button(label, key=f"btn_{cycle}_{cluster}", use_container_width=True):
                        st.session_state['sel_cycle'] = cycle
                        st.session_state['sel_cluster'] = cluster
                        st.session_state['nav_index'] = 2  # This triggers the jump to Ledger
                        st.rerun()
                    
                    st.markdown("</div>", unsafe_allow_html=True)

    # --- PAGE 2: DETAILS ---
    elif active_nav == "🔍 Details Discovery":
        st.subheader("AI Strategy Metrics")
        df = pd.DataFrame([vars(c) for c in view.processed_categories])
        if st.session_state['sel_cluster'] != "All Clusters":
            df = df[df['master_cluster'] == st.session_state['sel_cluster']]
        st.dataframe(df, use_container_width=True, hide_index=True)

    # --- PAGE 3: LEDGER ---
    elif active_nav == "📝 Transaction Ledger":
        st.subheader(f"Ledger: {st.session_state['sel_cycle']} | {st.session_state['sel_cluster']}")
        
        raw_df = st.session_state['raw_data'].copy()
        ai_map = pd.DataFrame([{'category': c.category, 'master_cluster': c.master_cluster} for c in view.processed_categories])
        ledger_df = raw_df.merge(ai_map, on='category', how='left')

        if st.session_state['sel_cycle'] != "All Cycles":
            ledger_df = ledger_df[ledger_df['cycle'] == st.session_state['sel_cycle']]
        if st.session_state['sel_cluster'] != "All Clusters":
            ledger_df = ledger_df[ledger_df['master_cluster'] == st.session_state['sel_cluster']]

        st.metric("Total", f"{ledger_df['amount'].sum():,.2f} €")
        st.dataframe(
            ledger_df[['cycle', 'master_cluster', 'category', 'label', 'amount']].sort_values('amount', ascending=False),
            use_container_width=True, hide_index=True
        )

# --- 6. GLOBAL EXPORT ---
if st.session_state.get('processed'):
    st.divider()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "rb") as f:
            st.download_button("📥 Download Excel Report", f, file_name="AI_Budget_Report.xlsx", use_container_width=True)