from typing import Dict, Sequence

from model.models import BudgetView, DataQualityReport, Transaction


class DataQualityService:
    """Evaluate cross-file quality rules after domain analysis."""

    @staticmethod
    def evaluate(
        transactions: Sequence[Transaction],
        category_cluster_map: Dict[str, str],
        budget_overrides: Dict[str, str],
        view: BudgetView,
        duplicate_transaction_count: int,
    ) -> DataQualityReport:
        transaction_categories = {item.category for item in transactions}
        auto_classified = tuple(
            sorted(transaction_categories - category_cluster_map.keys())
        )
        valid_budget_targets = transaction_categories | {
            item.master_cluster for item in view.processed_categories
        }
        unused_budget_targets = tuple(
            sorted(budget_overrides.keys() - valid_budget_targets)
        )
        return DataQualityReport(
            duplicate_transaction_count=duplicate_transaction_count,
            auto_classified_categories=auto_classified,
            unused_budget_targets=unused_budget_targets,
        )
