from dataclasses import dataclass
from typing import List

from application.data_quality_service import DataQualityService
from application.ports import (
    BudgetReader,
    MappingReader,
    ReportWriter,
    StrategyTuner,
    TransactionReader,
)
from model.models import (
    BudgetDomain,
    BudgetView,
    DataQualityReport,
    EnrichedTransaction,
)
from orchestrator import Orchestrator


@dataclass(frozen=True)
class AnalysisResult:
    view: BudgetView
    reporting_data: List[EnrichedTransaction]
    report_bytes: bytes
    quality: DataQualityReport


class AnalysisService:
    """Coordinate one analysis independently from UI and storage choices."""

    def __init__(
        self,
        transaction_reader: TransactionReader,
        mapping_reader: MappingReader,
        budget_reader: BudgetReader,
        report_writer: ReportWriter,
        strategy_tuner: StrategyTuner,
    ):
        self.transaction_reader = transaction_reader
        self.mapping_reader = mapping_reader
        self.budget_reader = budget_reader
        self.report_writer = report_writer
        self.strategy_tuner = strategy_tuner

    def analyze(
        self,
        bank_export: bytes,
        mapping_config: bytes,
        budget_config: bytes,
    ) -> AnalysisResult:
        transactions = self.transaction_reader.read(bank_export)
        category_cluster_map = self.mapping_reader.read(mapping_config)
        budget_overrides = self.budget_reader.read(budget_config)
        domain = BudgetDomain(
            transactions=transactions,
            category_cluster_map=category_cluster_map,
            budget_overrides=budget_overrides,
        )
        orchestrator = Orchestrator(domain)
        tuning = self.strategy_tuner.discover(orchestrator)
        view = orchestrator.run_analytics(tuning.strategy, tuning.config)
        quality = DataQualityService.evaluate(
            transactions,
            category_cluster_map,
            budget_overrides,
            view,
            self.transaction_reader.count_duplicates(bank_export),
        )
        return AnalysisResult(
            view=view,
            reporting_data=orchestrator.reporting_data,
            report_bytes=self.report_writer.write(view, orchestrator.reporting_data),
            quality=quality,
        )
