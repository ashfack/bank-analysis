import streamlit as st
import os
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

                # --- NEW: WEB DISPLAY LOGIC ---
                st.divider()
                st.subheader("📊 Executive Summary (Web View)")

                # Create 3 Top-level Metrics
                col1, col2, col3 = st.columns(3)
                total_spent = domain_data.transactions['amount'].sum()
                total_budget = sum(overrides.values()) # Simplified calculation

                with col1:
                    st.metric("Total Spent", f"{total_spent:,.2f} €")
                with col2:
                    st.metric("Theoretical Budget", f"{total_budget:,.2f} €")
                with col3:
                    delta = total_budget - total_spent
                    st.metric("Remaining", f"{delta:,.2f} €", delta_color="normal")

                # Display the Pivot Table with Heatmap styling
                st.write("### Spending by Cluster")

                # We grab the reporting data you already calculated
                df_summary = orch.reporting_data  

                # Simple coloring logic for the web table
                def color_budget(val):
                    color = 'red' if val > 1000 else 'green' # Example logic
                    return f'color: {color}'

                st.dataframe(df_summary.style.background_gradient(cmap='YlOrRd'), use_container_width=True)

                # Add a Plotly Chart for Evolution
                fig = px.bar(df_summary.T, title="Monthly Evolution by Category")
                st.plotly_chart(fig, use_container_width=True)
                
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