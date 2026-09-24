from collections import defaultdict
from typing import Sequence

from model.models import BudgetView, EnrichedTransaction, ProcessedCategory


class BudgetViewBuilder:
    """Project analyzed categories and transactions into the dashboard view."""

    @staticmethod
    def build(
        transactions: Sequence[EnrichedTransaction],
        categories: Sequence[ProcessedCategory],
    ) -> BudgetView:
        matrix = defaultdict(lambda: defaultdict(float))
        category_clusters = {
            category.category: category.master_cluster for category in categories
        }
        for transaction in transactions:
            cluster = category_clusters.get(transaction.category, "Unmapped")
            matrix[transaction.cycle][cluster] += transaction.amount

        cluster_budgets = defaultdict(float)
        for category in categories:
            cluster_budgets[category.master_cluster] += category.theoretical_budget

        return BudgetView(
            matrix={cycle: dict(values) for cycle, values in matrix.items()},
            cluster_budgets=dict(cluster_budgets),
            processed_categories=list(categories),
        )
