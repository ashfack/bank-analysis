from application.analysis_service import AnalysisResult, AnalysisService
from auto_tuner.strategy_auto_tuner import StrategyAutoTuner
from infrastructure.csv_readers import (
    BudgetCsvReader,
    MappingCsvReader,
    TransactionCsvReader,
)
from infrastructure.excel_report_writer import ExcelReportWriter


def run_uploaded_analysis(
    bank_export: bytes,
    mapping_config: bytes,
    budget_config: bytes,
) -> AnalysisResult:
    """Composition root for one uploaded analysis."""
    service = AnalysisService(
        transaction_reader=TransactionCsvReader(),
        mapping_reader=MappingCsvReader(),
        budget_reader=BudgetCsvReader(),
        report_writer=ExcelReportWriter(),
        strategy_tuner=StrategyAutoTuner(),
    )
    return service.analyze(bank_export, mapping_config, budget_config)
