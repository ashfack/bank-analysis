from config.config import BUDGET_FILE, INPUT_FILE, MAPPING_FILE, OUTPUT_FILE
from loader.data_loader import DataLoader
from model.models import BudgetDomain
from report_generator.excel_architect import ExcelArchitect
from orchestrator import Orchestrator
from auto_tuner.strategy_auto_tuner import StrategyAutoTuner


if __name__ == "__main__":
    transactions = DataLoader.prepare_transaction_data(INPUT_FILE)
    mapping = DataLoader.load_category_cluster_map(MAPPING_FILE)
    overrides = DataLoader.load_budget_overrides(BUDGET_FILE)


    # 2. Package into a single 'World State'
    domain_data = BudgetDomain(transactions, mapping, overrides)
    
    orch = Orchestrator(domain_data)
    
    # Run discovery with the new Leaderboard printout
    tuning = StrategyAutoTuner().discover(orch)
    
    view = orch.run_analytics(tuning.strategy, tuning.config)
    architect = ExcelArchitect(OUTPUT_FILE)
    architect.generate(view, orch.reporting_data)
    
    print(f"✅ V1 Budget Leaderboard generated.")
