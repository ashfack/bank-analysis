import streamlit as st
import pandas as pd
import os
from config.config import BUDGET_FILE, INPUT_FILE, MAPPING_FILE, OUTPUT_FILE
from loader.data_loader import DataLoader
from model.models import BudgetDomain
from orchestrator import Orchestrator
from auto_tuner.strategy_auto_tuner import StrategyAutoTuner

st.set_page_config(page_title="AI Budgeter", page_icon="📊", layout="wide")

# Session State Initialization
if 'processed' not in st.session_state:
    st.session_state['processed'] = False
if 'sel_cycle' not in st.session_state:
    st.session_state['sel_cycle'] = "All Cycles"
if 'sel_cluster' not in st.session_state:
    st.session_state['sel_cluster'] = "All Clusters"

# 1. Sidebar
with st.sidebar:
    st.title("🎯 Controls")
    
    if st.session_state['processed']:
        st.header("Focus Filter")
        # Source of truth is now the results from the Orchestrator pipeline
        df_raw = st.session_state['df_raw']
        
        raw_cycles = ["All Cycles"] + sorted(df_raw['cycle'].astype(str).unique().tolist(), reverse=True)
        raw_clusters = ["All Clusters"] + sorted(df_raw['master_cluster'].astype(str).unique().tolist())
        
        # Ensure selection persists during reruns
        st.session_state['sel_cycle'] = st.selectbox("Select Cycle:", raw_cycles, 
                                                     index=raw_cycles.index(st.session_state['sel_cycle']) if st.session_state['sel_cycle'] in raw_cycles else 0)
        st.session_state['sel_cluster'] = st.selectbox("Select Cluster:", raw_clusters, 
                                                       index=raw_clusters.index(st.session_state['sel_cluster']) if st.session_state['sel_cluster'] in raw_clusters else 0)
        st.divider()

    st.header("📂 Data Ingestion")
    bank_export = st.file_uploader("Operations (CSV)", type=['csv'])
    mapping_cfg = st.file_uploader("Mapping (CSV)", type=['csv'])
    budget_cfg = st.file_uploader("Budget (CSV)", type=['csv'])
    
    if st.button("🗑️ Reset All"):
        st.session_state.clear()
        st.rerun()

st.title("📊 AI-Powered Financial Orchestrator")

# 2. Processing
if st.button("🚀 Synchronize & Optimize", use_container_width=True):
    if bank_export and mapping_cfg and budget_cfg:
        try:
            os.makedirs(os.path.dirname(INPUT_FILE), exist_ok=True)
            for path, file in {INPUT_FILE: bank_export, MAPPING_FILE: mapping_cfg, BUDGET_FILE: budget_cfg}.items():
                with open(path, "wb") as f: f.write(file.getbuffer())

            with st.spinner("🧠 Analyzing Data via AI Orchestrator..."):
                # Load using your DataLoader[cite: 4]
                transactions = DataLoader.prepare_transaction_data(INPUT_FILE)
                mapping = DataLoader.load_category_cluster_map(MAPPING_FILE)
                overrides = DataLoader.load_budget_overrides(BUDGET_FILE)
                domain_data = BudgetDomain(transactions, mapping, overrides)
                
                # Run AI Discovery & Pipeline[cite: 2, 4]
                orch = Orchestrator(domain_data)
                best_strat, best_params = StrategyAutoTuner.discover(orch)
                final_stats = orch.run_pipeline(best_strat, best_params)

                # Convert AI results (ProcessedCategory) to DataFrame[cite: 1]
                df_stats = pd.DataFrame([vars(s) for s in final_stats])
                
                # Merge the AI-discovered clusters into the raw reporting data
                df_raw = pd.DataFrame(orch.reporting_data)
                # We use the results of the pipeline to define the clusters for the UI
                ai_mapping = df_stats[['category', 'master_cluster']]
                df_raw = df_raw.merge(ai_mapping, on='category', how='left')

                st.session_state['df_stats'] = df_stats
                st.session_state['df_raw'] = df_raw
                st.session_state['processed'] = True
                st.rerun()
        except Exception as e:
            st.error(f"Error during AI Orchestration: {e}")

# 3. Interactive Views
if st.session_state.get('processed'):
    # Logic for Tab Jumping
    start_tab = 2 if st.session_state.get('jump_to_ledger') else 0
    st.session_state['jump_to_ledger'] = False

    tab_pilotage, tab_details, tab_ledger = st.tabs(["📑 Pilotage", "🔍 Details", "📝 Ledger"])

    with tab_pilotage:
        st.subheader("Interactive Drill-Down Grid")
        
        # Pivot based on the AI-discovered clusters
        pivot = st.session_state['df_raw'].pivot_table(
            index='cycle', columns='master_cluster', values='amount', aggfunc='sum', fill_value=0
        )
        
        cycles = sorted(pivot.index.tolist(), reverse=True)
        clusters = sorted(pivot.columns.tolist())

        # Grid Rendering (Clickable Cells)
        cols = st.columns([1.5] + [1] * len(clusters))
        cols[0].write("**Cycle**")
        for i, cluster in enumerate(clusters):
            cols[i+1].write(f"**{cluster}**")

        for cycle in cycles:
            cols = st.columns([1.5] + [1] * len(clusters))
            cols[0].write(cycle)
            for i, cluster in enumerate(clusters):
                val = pivot.loc[cycle, cluster]
                if cols[i+1].button(f"{val:,.0f} €" if val > 0 else "—", key=f"{cycle}_{cluster}", use_container_width=True):
                    st.session_state['sel_cycle'] = str(cycle)
                    st.session_state['sel_cluster'] = str(cluster)
                    st.session_state['jump_to_ledger'] = True
                    st.rerun()

    with tab_details:
        st.subheader("AI Strategy Stats per Category")
        stats_view = st.session_state['df_stats']
        if st.session_state['sel_cluster'] != "All Clusters":
            stats_view = stats_view[stats_view['master_cluster'] == st.session_state['sel_cluster']]
        st.dataframe(stats_view, use_container_width=True, hide_index=True)

    with tab_ledger:
        st.subheader(f"Ledger: {st.session_state['sel_cycle']} | {st.session_state['sel_cluster']}")
        ledger_df = st.session_state['df_raw']
        
        if st.session_state['sel_cycle'] != "All Cycles":
            ledger_df = ledger_df[ledger_df['cycle'].astype(str) == st.session_state['sel_cycle']]
        if st.session_state['sel_cluster'] != "All Clusters":
            ledger_df = ledger_df[ledger_df['master_cluster'].astype(str) == st.session_state['sel_cluster']]
            
        st.metric("Total Sum", f"{ledger_df['amount'].sum():,.2f} €")
        st.dataframe(ledger_df[['cycle', 'category', 'label', 'amount']], use_container_width=True, hide_index=True)