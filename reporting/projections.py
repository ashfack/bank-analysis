from typing import Sequence

import pandas as pd

from model.models import BudgetView, EnrichedTransaction


def build_category_table(view: BudgetView) -> pd.DataFrame:
    """Project processed domain categories into a presentation-neutral table."""
    return pd.DataFrame([vars(category) for category in view.processed_categories])


def build_ledger_table(
    view: BudgetView,
    transactions: Sequence[EnrichedTransaction],
) -> pd.DataFrame:
    """Attach the resolved master cluster to each enriched transaction."""
    table = pd.DataFrame([vars(transaction) for transaction in transactions])
    category_clusters = {
        category.category: category.master_cluster
        for category in view.processed_categories
    }
    table["master_cluster"] = table["category"].map(category_clusters)
    return table
