import streamlit as st
import pandas as pd
import os
from config.config import BUDGET_FILE, INPUT_FILE, MAPPING_FILE, OUTPUT_FILE
from loader.data_loader import DataLoader
from model.models import BudgetDomain
from report_generator.excel_architect import ExcelArchitect
from orchestrator import Orchestrator
from auto_tuner.strategy_auto_tuner import StrategyAutoTuner

# 1. Page Configuration
st.set_page_config(
    page_title="Awesome Budgeter AI", 
    page_icon="🤖", 
    layout="wide"
)

st.title("📊 Awesome Budgeter: AI-Tuned Reporting")
st.markdown("""
    Upload your raw bank exports and configuration files. 
    The **Auto-Tuner** will automatically find the best budget strategy for your spending patterns.
""")

# 2. Sidebar / File Uploaders
with st.sidebar:
    st.header("📂 Data Upload")
    bank_export = st.file_uploader("Bank Operations (CSV)", type=['csv'])
    mapping_cfg = st.file_uploader("Mapping Config (CSV)", type=['csv'])
    budget_cfg = st.file_uploader("Budget Config (CSV)", type=['csv'])
    
    st.divider()
    st.info("The Auto-Tuner evaluates multiple strategies (Z-Score, Median, etc.) to minimize budget variance.")

# 3. Main Execution Logic
if st.button("🚀 Run Auto-Tuner & Generate Report", use_container_width=True):
    if bank_export and mapping_cfg and budget_cfg:
        try:
            # Create directories if they don't exist
            os.makedirs(os.path.dirname(INPUT_FILE), exist_ok=True)
            os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

            # Save uploaded files to the paths defined in config.py
            files_to_save = {
                INPUT_FILE: bank_export,
                MAPPING_FILE: mapping_cfg,
                BUDGET_FILE: budget_cfg
            }
            
            for path, uploaded_file in files_to_save.items():
                with open(path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

            with st.spinner("🧠 AI Auto-Tuning in progress..."):
                # --- MIRRORING YOUR main.py LOGIC ---
                
                # A. Load Data
                transactions = DataLoader.prepare_transaction_data(INPUT_FILE)
                mapping = DataLoader.load_category_cluster_map(MAPPING_FILE)
                overrides = DataLoader.load_budget_overrides(BUDGET_FILE)
                domain_data = BudgetDomain(transactions, mapping, overrides)
                
                # B. Orchestration & Discovery
                orch = Orchestrator(domain_data)
                best_strat, best_params = StrategyAutoTuner.discover(orch)
                
                # C. Final Pipeline Run
                final_stats = orch.run_pipeline(best_strat, best_params)

                # D. Generate Physical Excel File
                architect = ExcelArchitect(domain_data.transactions, final_stats, OUTPUT_FILE)
                architect.generate(orch.reporting_data)

            # --- 4. WEB DASHBOARD RENDERING ---
            st.success(f"✅ Optimization Complete! Best Strategy: **{best_strat}**")
            
            # Convert DTO objects to a DataFrame for Streamlit
            df_stats = pd.DataFrame([vars(s) for s in final_stats])
            
            # Row 1: Key Performance Indicators
            tot_spent = df_stats['total_actual_spending'].sum()
            tot_budget = df_stats['theoretical_budget'].sum()
            variance = tot_budget - tot_spent
            
            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric("Total Actual Spending", f"{tot_spent:,.2f} €")
            kpi2.metric("AI-Calculated Budget", f"{tot_budget:,.2f} €")
            kpi3.metric("Overall Variance", f"{variance:,.2f} €", delta_color="normal")

            # Row 2: Visualizations
            col_left, col_right = st.columns([1, 1])

            with col_left:
                st.write("### 🏗️ Spending by Cluster")
                # Aggregate stats by cluster
                cluster_df = df_stats.groupby('master_cluster').agg({
                    'total_actual_spending': 'sum',
                    'theoretical_budget': 'sum'
                }).sort_values('total_actual_spending', ascending=False)
                
                st.dataframe(
                    cluster_df.style.background_gradient(cmap='YlGnBu', axis=0),
                    use_container_width=True
                )

            with col_right:
                st.write("### 📈 Cycle Evolution")
                # Transform reporting_data (list of dicts) into a pivot for charting
                df_raw = pd.DataFrame(orch.reporting_data)
                if not df_raw.empty:
                    pivot_ev = df_raw.pivot_table(
                        index='cycle', 
                        columns='category', 
                        values='amount', 
                        aggfunc='sum'
                    ).fillna(0)
                    st.line_chart(pivot_ev)

            # Row 3: Download Section
            st.divider()
            with open(OUTPUT_FILE, "rb") as file:
                st.download_button(
                    label="📥 Download Full Excel Report (V1 Budget Leaderboard)",
                    data=file,
                    file_name="Optimized_Budget_Report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

        except Exception as e:
            st.error(f"❌ Critical Error during orchestration: {e}")
            st.exception(e) # Provides a traceback for easier debugging on HF
    else:
        st.warning("⚠️ Please upload all three configuration files in the sidebar to begin.")

# 4. Footer
st.markdown("---")
st.caption("Bank Analysis Engine v1.0 | Powered by StrategyAutoTuner")