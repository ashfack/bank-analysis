import streamlit as st
import pandas as pd
from analysis_runner import run_uploaded_analysis
from dashboard import build_pilotage_table, style_pilotage_table

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
    st.session_state['nav_index'] = 0 

# --- 3. SIDEBAR: NAVIGATION ---
with st.sidebar:
    st.title("🎯 Control Panel")
    
    nav_options = ["📑 Pilotage", "🔍 Details Discovery", "📝 Transaction Ledger"]
    active_nav = st.radio("Navigation", nav_options, index=st.session_state['nav_index'])
    st.session_state['nav_index'] = nav_options.index(active_nav)

    st.divider()

    if st.session_state['processed']:
        st.header("Focus Filter")
        view = st.session_state['budget_view']
        cycles_list = ["All Cycles"] + view.cycles
        clusters_list = ["All Clusters"] + view.clusters
        
        st.session_state['sel_cycle'] = st.selectbox("Select Cycle:", cycles_list, 
            index=cycles_list.index(st.session_state['sel_cycle']) if st.session_state['sel_cycle'] in cycles_list else 0)
        st.session_state['sel_cluster'] = st.selectbox("Select Cluster:", clusters_list, 
            index=clusters_list.index(st.session_state['sel_cluster']) if st.session_state['sel_cluster'] in clusters_list else 0)

    st.header("📂 Data Ingestion")
    bank_export = st.file_uploader("Operations (CSV)", type=['csv'])
    mapping_cfg = st.file_uploader("Mapping (CSV)", type=['csv'])
    budget_cfg = st.file_uploader("Budget (CSV)", type=['csv'])
    
    if st.button("🗑️ Reset Application"):
        st.session_state.clear()
        st.rerun()

st.title("📊 AI-Powered Financial Orchestrator")

# --- 4. EXECUTION ENGINE ---
if st.button("🚀 Synchronize & Optimize", width="stretch"):
    if bank_export and mapping_cfg and budget_cfg:
        try:
            with st.spinner("🧠 Orchestrating Domain Logic..."):
                result = run_uploaded_analysis(
                    bank_export.getvalue(),
                    mapping_cfg.getvalue(),
                    budget_cfg.getvalue(),
                )

                st.session_state['budget_view'] = result.view
                st.session_state['raw_data'] = pd.DataFrame(result.reporting_data)
                st.session_state['report_bytes'] = result.report_bytes
                st.session_state['duplicate_transaction_count'] = (
                    result.duplicate_transaction_count
                )
                st.session_state['processed'] = True
                st.rerun()
        except Exception as e:
            st.error(f"Orchestration Error: {e}")

# --- 5. DASHBOARD VIEW ADAPTER ---
if st.session_state.get('processed'):
    view = st.session_state['budget_view']

    duplicate_count = st.session_state.get('duplicate_transaction_count', 0)
    if duplicate_count:
        st.warning(
            f"Qualité des données : {duplicate_count} ligne(s) d'opération "
            "strictement identique(s) ont été détectée(s). Elles restent "
            "incluses dans les calculs."
        )
    
    # --- PAGE 1: PILOTAGE ---
    if active_nav == "📑 Pilotage":
        st.subheader("Master Cluster Time-Series")
        st.caption("Sélectionnez une cellule de dépense pour ouvrir les opérations correspondantes.")
        pilotage_table = build_pilotage_table(view)
        column_config = {
            "Cycle": st.column_config.TextColumn("Cycle", width="medium"),
            **{
                cluster: st.column_config.NumberColumn(cluster, format="%.0f €", width="small")
                for cluster in view.clusters
            },
        }
        pilotage_event = st.dataframe(
            style_pilotage_table(pilotage_table, view),
            width="stretch",
            height=720,
            hide_index=True,
            column_config=column_config,
            key="pilotage_table",
            on_select="rerun",
            selection_mode="single-cell",
            placeholder="—",
        )

        if pilotage_event.selection.cells:
            row_index, cluster = pilotage_event.selection.cells[0]
            if row_index > 0 and cluster != "Cycle":
                cycle = pilotage_table.iloc[row_index]["Cycle"]
                if view.get_amount(cycle, cluster) > 0:
                    st.session_state['sel_cycle'] = cycle
                    st.session_state['sel_cluster'] = cluster
                    st.session_state['nav_index'] = 2
                    st.rerun()

    # --- PAGE 2: DETAILS ---
    elif active_nav == "🔍 Details Discovery":
        st.subheader("AI Strategy Metrics")
        df = pd.DataFrame([vars(c) for c in view.processed_categories])
        if st.session_state['sel_cluster'] != "All Clusters":
            df = df[df['master_cluster'] == st.session_state['sel_cluster']]
        st.dataframe(df, width="stretch", hide_index=True)

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
        st.dataframe(ledger_df[['cycle', 'master_cluster', 'category', 'label', 'amount']].sort_values('amount', ascending=False),
            width="stretch", hide_index=True)

# --- 6. GLOBAL EXPORT ---
if st.session_state.get('processed'):
    st.divider()
    st.download_button(
        "📥 Download Excel Report",
        st.session_state['report_bytes'],
        file_name="AI_Budget_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
    )
