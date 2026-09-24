from typing import List

from config.config import ANCHOR_CATEGORY, BudgetStrategy
from domain.budget_allocator import BudgetAllocator
from domain.budget_view_builder import BudgetViewBuilder
from domain.category_analyzer import CategoryAnalyzer
from domain.cycle_assigner import CycleAssigner
from model.models import (
    BudgetDomain,
    BudgetView,
    EnrichedTransaction,
    ProcessedCategory,
    StrategyConfig,
)


class Orchestrator:
    """Coordinate the domain services required to build a budget view."""

    def __init__(self, domain: BudgetDomain):
        self.domain = domain
        self.transactions = domain.transactions
        self.overrides = domain.budget_overrides
        self.category_analyzer = CategoryAnalyzer(
            domain.category_cluster_map,
            domain.budget_overrides,
        )
        self.budget_allocator = BudgetAllocator()
        self.view_builder = BudgetViewBuilder()
        self._enriched_data = CycleAssigner(ANCHOR_CATEGORY).assign(self.transactions)

    @property
    def reporting_data(self) -> List[EnrichedTransaction]:
        return self._enriched_data

    def run_analytics(
        self,
        strategy: BudgetStrategy,
        config: StrategyConfig,
    ) -> BudgetView:
        categories = self.run_pipeline(strategy, config)
        return self.view_builder.build(self._enriched_data, categories)

    def run_pipeline(
        self,
        strategy: BudgetStrategy,
        config: StrategyConfig,
    ) -> List[ProcessedCategory]:
        categories = self.category_analyzer.analyze(
            self._enriched_data,
            strategy,
            config,
        )
        return self.budget_allocator.apply(categories, self.overrides)
