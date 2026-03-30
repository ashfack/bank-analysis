import streamlit as st
import os
import pandas as pd
import plotly.express as px
from config.config import BUDGET_FILE, INPUT_FILE, MAPPING_FILE, OUTPUT_FILE
from loader.data_loader import DataLoader
from model.models import BudgetDomain
from report_generator.excel_architect import ExcelArchitect
from orchestrator import Orchestrator
from auto_tuner.strategy_auto_tuner import StrategyAutoTuner

st.set_page_config(page_title="Awesome Budgeter AI", page_icon="🤖")
st.title("🤖 Awesome Budgeter: AI-Tuned Reporting")

# 1. File Uploaders
col1, col2, col3 = st.columns(3)
with col1:
    bank_export = st.file_uploader("Bank Operations", type=['csv'])
with col2:
    mapping_cfg = st.file_uploader("Mapping Config", type=['csv'])
with col3:
    budget_cfg = st.file_uploader("Budget Config", type=['csv'])

if st.button("🚀 Run Auto-Tuner & Generate Report", use_container_width=True):
    if bank_export and mapping_cfg and budget_cfg:
        try:
            with st.spinner("🔍 Discovering best strategy..."):
                # Save files to paths defined in your config.py
                os.makedirs(os.path.dirname(INPUT_FILE), exist_ok=True)
                os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

                for uploaded_file, target_path in zip(
                    [bank_export, mapping_cfg, budget_cfg], 
                    [INPUT_FILE, MAPPING_FILE, BUDGET_FILE]
                ):
                    with open(target_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                # --- REPLICATING YOUR main.py LOGIC ---
                # 1. Load Data
                transactions = DataLoader.prepare_transaction_data(INPUT_FILE)
                mapping = DataLoader.load_category_cluster_map(MAPPING_FILE)
                overrides = DataLoader.load_budget_overrides(BUDGET_FILE)
                domain_data = BudgetDomain(transactions, mapping, overrides)
                
                # 2. Orchestrate & Tune
                orch = Orchestrator(domain_data)
                best_strat, best_params = StrategyAutoTuner.discover(orch)
                
                # 3. Run Pipeline
                st.info(f"✨ Best Strategy Found: {best_strat}")
                final_stats = orch.run_pipeline(best_strat, best_params)

                # 4. Generate Excel
                architect = ExcelArchitect(domain_data.transactions, final_stats, OUTPUT_FILE)
                architect.generate(orch.reporting_data)

                # --- REVISED WEB DISPLAY LOGIC ---
                st.divider()
                st.subheader("📊 Executive Summary (Web View)")

                try:
                    # 1. Handle Transactions (converting list of models to DF if necessary)
                    if isinstance(domain_data.transactions, list):
                        df_tx = pd.DataFrame([vars(t) for t in domain_data.transactions])
                    else:
                        df_tx = domain_data.transactions

                    # 2. Calculate Top-level Metrics
                    total_spent = df_tx['amount'].abs().sum() 
                    # Use your actual budget values from the overrides dict
                    total_budget = sum(overrides.values()) if isinstance(overrides, dict) else 0

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Spent", f"{total_spent:,.2f} €")
                    with col2:
                        st.metric("Theoretical Budget", f"{total_budget:,.2f} €")
                    with col3:
                        delta = total_budget - total_spent
                        st.metric("Remaining", f"{delta:,.2f} €", delta_color="normal")

                    # 3. Display the Pivot Table (Reporting Data)
                    st.write("### Spending by Cluster")
                    
                    # Ensure reporting_data is a DataFrame for display
                    df_summary = orch.reporting_data
                    if isinstance(df_summary, pd.DataFrame):
                        st.dataframe(df_summary.style.background_gradient(axis=0, cmap='YlOrRd'), use_container_width=True)
                        
                        # 4. Interactive Bar Chart
                        import plotly.express as px
                        # Transpose so months are on X-axis and Clusters are the legend
                        fig = px.bar(df_summary.T, barmode='group', title="Monthly Spending Trends")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No pivot data available for display.")

                except Exception as visual_err:
                    st.warning(f"Note: UI Summary couldn't render, but your Excel is ready. Error: {visual_err}")
                
                # --- REVISED WEB DISPLAY LOGIC ---

                st.success("✅ V1 Budget Leaderboard generated!")

                # 5. Download Button
                with open(OUTPUT_FILE, "rb") as file:
                    st.download_button(
                        label="📥 Download Professional Report",
                        data=file,
                        file_name="Budgeted_Report.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        except Exception as e:
            st.error(f"Error during orchestration: {e}")
    else:
        st.warning("Please upload all three files to begin.")