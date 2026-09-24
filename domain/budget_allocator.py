from dataclasses import replace
from typing import Any, Dict, Sequence

from budgeter.budget_custom_overrider import SymbolicOverride
from model.models import ProcessedCategory


class BudgetAllocator:
    """Apply cluster-level budget rules to analyzed categories."""

    def apply(
        self,
        categories: Sequence[ProcessedCategory],
        overrides: Dict[str, str],
    ) -> list[ProcessedCategory]:
        category_names = {category.category for category in categories}
        allocated = list(categories)
        for target, rule in overrides.items():
            if target not in category_names:
                allocated = self.update_cluster(allocated, target, rule)
        return allocated

    def update_cluster(
        self,
        categories: Sequence[ProcessedCategory],
        cluster_name: str,
        rule: Any,
    ) -> list[ProcessedCategory]:
        members = [
            category
            for category in categories
            if category.master_cluster == cluster_name
        ]
        if not members:
            return list(categories)

        values = self.calculate_distribution(members, rule)
        allocated_values = dict(zip((item.category for item in members), values))
        return [
            replace(category, theoretical_budget=allocated_values[category.category])
            if category.category in allocated_values
            else category
            for category in categories
        ]

    @staticmethod
    def calculate_distribution(
        members: Sequence[ProcessedCategory],
        rule: Any,
    ) -> list[float]:
        if str(rule).replace(".", "", 1).isdigit():
            median_sum = sum(member.median for member in members)
            return [
                member.median / median_sum * float(rule)
                if median_sum > 0
                else float(rule) / len(members)
                for member in members
            ]
        return [SymbolicOverride.apply(rule, member.base_limit) for member in members]
