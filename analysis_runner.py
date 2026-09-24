from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, List

from auto_tuner.strategy_auto_tuner import StrategyAutoTuner
from loader.data_loader import DataLoader
from model.models import BudgetDomain, BudgetView
from orchestrator import Orchestrator
from report_generator.excel_architect import ExcelArchitect


@dataclass(frozen=True)
class AnalysisResult:
    view: BudgetView
    reporting_data: List[Dict[str, Any]]
    report_bytes: bytes


def run_uploaded_analysis(
    bank_export: bytes,
    mapping_config: bytes,
    budget_config: bytes,
) -> AnalysisResult:
    """Run one uploaded analysis without using shared application files."""
    with TemporaryDirectory(prefix="bank-analysis-") as workspace:
        workspace_path = Path(workspace)
        input_path = workspace_path / "export-operations.csv"
        mapping_path = workspace_path / "mapping-config.csv"
        budget_path = workspace_path / "budget-config.csv"
        output_path = workspace_path / "budget-report.xlsx"

        input_path.write_bytes(bank_export)
        mapping_path.write_bytes(mapping_config)
        budget_path.write_bytes(budget_config)

        domain = BudgetDomain(
            transactions=DataLoader.prepare_transaction_data(str(input_path)),
            category_cluster_map=DataLoader.load_category_cluster_map(str(mapping_path)),
            budget_overrides=DataLoader.load_budget_overrides(str(budget_path)),
        )
        orchestrator = Orchestrator(domain)
        strategy, strategy_config = StrategyAutoTuner.discover(orchestrator)
        view = orchestrator.run_analytics(strategy, strategy_config)

        ExcelArchitect(str(output_path)).generate(view, orchestrator.reporting_data)

        return AnalysisResult(
            view=view,
            reporting_data=orchestrator.reporting_data,
            report_bytes=output_path.read_bytes(),
        )
