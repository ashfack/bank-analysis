from collections import defaultdict
from dataclasses import replace
import math
from typing import Any, Dict, List

from budgeter.budget_custom_overrider import SymbolicOverride
from budgeter.strategy_registry import StrategyRegistry
from categorizer.categorizer import Categorizer
from config.config import ANCHOR_CATEGORY, BudgetStrategy
from model.models import BudgetDomain, CategoryStats, ProcessedCategory, StrategyConfig


class Orchestrator:
    def __init__(self, domain: BudgetDomain):
        self.transactions = domain.transactions
        self.overrides = domain.budget_overrides
        self.categorizer = Categorizer(domain.category_cluster_map)
        self._enriched_data = self._define_cycles()

    @property
    def reporting_data(self) -> List[Dict[str, Any]]:
        return self._enriched_data
    
    def _define_cycles(self) -> List[Dict[str, Any]]:
        """Identifies pay cycles and preserves original signs for categorization."""
        pay_dates = sorted({
            t.dateOperation for t in self.transactions 
            if t.category == ANCHOR_CATEGORY
        })
        
        enriched = []
        for t in self.transactions:
            past_anchors = [p for p in pay_dates if p <= t.dateOperation]
            cycle_label = f"Cycle_du_{max(past_anchors).strftime('%Y-%m-%d')}" if past_anchors else "Initial"
            
            enriched.append({
                'category': t.category,
                'amount': abs(t.amount),
                'raw_amount': t.amount,
                'label': t.label,
                'cycle': cycle_label
            })
        return enriched

    def run_pipeline(self, strategy: BudgetStrategy, config: StrategyConfig) -> List[ProcessedCategory]:
        """Main entry point: Transform transactions to DTOs, then apply global rules."""
        results = self._process_all_categories(strategy, config)
        return self._apply_global_overrides(results)

    def _process_all_categories(self, strategy, config) -> List[ProcessedCategory]:
        """Groups data and maps each category to a ProcessedCategory DTO."""
        grouped = self._group_by_category()
        cycle_count = len({item['cycle'] for item in self._enriched_data})

        return [
            self._create_dto(cat, data, cycle_count, strategy, config)
            for cat, data in grouped.items()
        ]

    def _apply_global_overrides(self, results: List[ProcessedCategory]) -> List[ProcessedCategory]:
        """Iterates through overrides and updates the list if it's a cluster-level rule."""
        category_names = {r.category for r in results}
        current_results = results[:]

        for target, rule in self.overrides.items():
            if target not in category_names:
                current_results = self._update_cluster(current_results, target, rule)
                    
        return current_results

    def _update_cluster(self, results: List[ProcessedCategory], cluster_name: str, rule: Any) -> List[ProcessedCategory]:
        """Finds members of a cluster and returns a new list with updated frozen DTOs."""
        members = [r for r in results if r.master_cluster == cluster_name]
        if not members:
            return results

        # 1. Calculate the new values for the whole cluster
        new_values = self._calculate_distribution(members, rule)
        val_map = dict(zip([m.category for m in members], new_values))

        # 2. Return a new list with replaced objects where necessary
        return [
            replace(r, theoretical_budget=val_map[r.category]) if r.category in val_map else r 
            for r in results
        ]

    def _calculate_distribution(self, members: List[ProcessedCategory], rule: Any) -> List[float]:
        """Pure math: Returns a list of floats representing the new budgets."""
        if str(rule).replace('.', '', 1).isdigit():
            m_sum = sum(m.median for m in members)
            return [
                (m.median / m_sum * float(rule)) if m_sum > 0 else (float(rule) / len(members))
                for m in members
            ]
        return [SymbolicOverride.apply(rule, m.base_limit) for m in members]

    def _group_by_category(self) -> Dict[str, Dict]:
        groups = defaultdict(lambda: {"cycles": defaultdict(float), "sample": None, "total": 0.0})
        for item in self._enriched_data:
            c = groups[item['category']]
            c["cycles"][item['cycle']] += item['amount']
            c["total"] += item['amount']
            if not c["sample"]:
                c["sample"] = {'label': item['label'], 'amount': item['raw_amount']}
        return groups

    def _create_dto(self, name, data, total_cycles, strategy, config) -> ProcessedCategory:
        history = list(data["cycles"].values())
        stats = self._calculate_stats(history, total_cycles)
        
        cluster = self.categorizer.classify(name, stats, data["sample"]['label'], data["sample"]['amount'])
        base_limit = StrategyRegistry.compute_atomic(strategy, history, stats, config)
        
        return ProcessedCategory(
            category=name, master_cluster=cluster,
            median=stats.median, std_dev=stats.std, count=stats.count, frequency=stats.frequency,
            base_limit=base_limit,
            theoretical_budget=SymbolicOverride.apply(self.overrides.get(name), base_limit),
            total_actual_spending=round(data["total"], 2)
        )

    def _calculate_stats(self, history: List[float], total_cycles: int) -> CategoryStats:
        n = len(history)
        sorted_h = sorted(history)
        median = sorted_h[n//2] if n % 2 != 0 else sum(sorted_h[n//2-1:n//2+1])/2
        mean = sum(history) / n
        std = math.sqrt(sum((x - mean)**2 for x in history) / n)
        return CategoryStats(float(median), float(std), n, float(n/total_cycles) if total_cycles else 0.0)

    def _define_cycles(self) -> List[Dict[str, Any]]:
        pay_dates = sorted({t.dateOperation for t in self.transactions if t.category == ANCHOR_CATEGORY})
        enriched = []
        for t in self.transactions:
            past = [p for p in pay_dates if p <= t.dateOperation]
            lbl = f"Cycle_du_{max(past).strftime('%Y-%m-%d')}" if past else "Initial"
            enriched.append({'category': t.category, 'amount': abs(t.amount), 'raw_amount': t.amount, 'label': t.label, 'cycle': lbl})
        return enriched