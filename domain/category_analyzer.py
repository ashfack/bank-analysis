from collections import defaultdict
import math
from typing import Any, Dict, Sequence

from budgeter.budget_custom_overrider import SymbolicOverride
from budgeter.strategy_registry import StrategyRegistry
from categorizer.categorizer import Categorizer
from config.config import BudgetStrategy
from model.models import (
    CategoryStats,
    EnrichedTransaction,
    ProcessedCategory,
    StrategyConfig,
)


class CategoryAnalyzer:
    """Compute category statistics, classifications and atomic budgets."""

    def __init__(self, category_cluster_map: Dict[str, str], overrides: Dict[str, str]):
        self.categorizer = Categorizer(category_cluster_map)
        self.overrides = overrides

    def analyze(
        self,
        transactions: Sequence[EnrichedTransaction],
        strategy: BudgetStrategy,
        config: StrategyConfig,
    ) -> list[ProcessedCategory]:
        grouped = self._group_by_category(transactions)
        cycle_count = len({item.cycle for item in transactions})
        return [
            self._create_category(name, data, cycle_count, strategy, config)
            for name, data in grouped.items()
        ]

    @staticmethod
    def calculate_stats(history: list[float], total_cycles: int) -> CategoryStats:
        count = len(history)
        sorted_history = sorted(history)
        median = (
            sorted_history[count // 2]
            if count % 2 != 0
            else sum(sorted_history[count // 2 - 1 : count // 2 + 1]) / 2
        )
        mean = sum(history) / count
        std = math.sqrt(sum((value - mean) ** 2 for value in history) / count)
        frequency = float(count / total_cycles) if total_cycles else 0.0
        return CategoryStats(float(median), float(std), count, frequency)

    @staticmethod
    def _group_by_category(
        transactions: Sequence[EnrichedTransaction],
    ) -> Dict[str, Dict[str, Any]]:
        groups = defaultdict(
            lambda: {"cycles": defaultdict(float), "sample": None, "total": 0.0}
        )
        for item in transactions:
            category = groups[item.category]
            category["cycles"][item.cycle] += item.amount
            category["total"] += item.amount
            if not category["sample"]:
                category["sample"] = {
                    "label": item.label,
                    "amount": item.raw_amount,
                }
        return groups

    def _create_category(
        self,
        name: str,
        data: Dict[str, Any],
        total_cycles: int,
        strategy: BudgetStrategy,
        config: StrategyConfig,
    ) -> ProcessedCategory:
        history = list(data["cycles"].values())
        stats = self.calculate_stats(history, total_cycles)
        cluster = self.categorizer.classify(
            name,
            stats,
            data["sample"]["label"],
            data["sample"]["amount"],
        )
        base_limit = StrategyRegistry.compute_atomic(strategy, history, stats, config)
        return ProcessedCategory(
            category=name,
            master_cluster=cluster,
            median=stats.median,
            std_dev=stats.std,
            count=stats.count,
            frequency=stats.frequency,
            base_limit=base_limit,
            theoretical_budget=SymbolicOverride.apply(
                self.overrides.get(name), base_limit
            ),
            total_actual_spending=round(data["total"], 2),
        )
