import streamlit as st
import pandas as pd
from analysis_runner import run_uploaded_analysis

# --- 1. SHARED STYLING LOGIC ---
def get_budget_color(val: float, limit: float, cluster: str) -> str:
    # Use .startswith() to avoid matching "10." or "20."
    is_income_or_internal = cluster.startswith("0.")
    
    if val == 0:
        return "#FFFFFF"
        
    if is_income_or_internal:
        return "#548235" # Always green for income/internal if > 0
    
    # Standard budget logic for expense clusters (1, 2, 3...)
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
if st.button("🚀 Synchronize & Optimize", use_container_width=True):
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

        h_cols = st.columns([1.5] + [1] * len(clusters))
        h_cols[0].write("**Cycle**")
        for idx, cluster in enumerate(clusters):
            h_cols[idx+1].markdown(f"<div style='text-align: center'><b>{cluster}</b></div>", unsafe_allow_html=True)

        b_cols = st.columns([1.5] + [1] * len(clusters))
        b_cols[0].markdown("*:blue[BUDGET THEORIQUE]*")
        for idx, cluster in enumerate(clusters):
            val = view.get_budget(cluster)
            b_cols[idx+1].markdown(f"<div style='text-align: center; color: #1E90FF;'><b>{val:,.0f} €</b></div>", unsafe_allow_html=True)
        
        st.divider()

        for cycle in cycles:
            r_cols = st.columns([1.5] + [1] * len(clusters))
            r_cols[0].write(f"**{cycle}**")
            for idx, cluster in enumerate(clusters):
                val = view.get_amount(cycle, cluster)
                limit = view.get_budget(cluster)
                bg = get_budget_color(val, limit, cluster)
                
                with r_cols[idx+1]:
                    st.markdown(f"""<div style="background-color: {bg}; border-radius: 4px; padding: 2px;">""", unsafe_allow_html=True)
                    label = f"{val:,.0f} €" if val > 0 else "—"
                    if st.button(label, key=f"btn_{cycle}_{cluster}", use_container_width=True):
                        st.session_state['sel_cycle'] = cycle
                        st.session_state['sel_cluster'] = cluster
                        st.session_state['nav_index'] = 2 
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
        st.dataframe(ledger_df[['cycle', 'master_cluster', 'category', 'label', 'amount']].sort_values('amount', ascending=False),
            use_container_width=True, hide_index=True)

# --- 6. GLOBAL EXPORT ---
if st.session_state.get('processed'):
    st.divider()
    st.download_button(
        "📥 Download Excel Report",
        st.session_state['report_bytes'],
        file_name="AI_Budget_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
