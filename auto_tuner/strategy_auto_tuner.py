import itertools
import math
from typing import Tuple, List, Dict
from collections import defaultdict

from config.config import ACTIVE_STRATEGY, MANUAL_MODE, MANUAL_PARAMS, BudgetStrategy
from model.models import BudgetDomain, StrategyConfig, ProcessedCategory
# Note: Using Type Hinting for Orchestrator to avoid circular imports if necessary
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from orchestrator import Orchestrator

class StrategyAutoTuner:
    """Responsibility: Discovery with detailed Parameter Leaderboard (Pure Python)"""
    
    @staticmethod
    def discover(orchestrator: "Orchestrator") -> Tuple[BudgetStrategy, StrategyConfig]:
        if MANUAL_MODE: 
            return ACTIVE_STRATEGY, MANUAL_PARAMS

        training_orchestrator, cycle_history = StrategyAutoTuner._prepare_temporal_validation(orchestrator)

        # Historical ground truth contains only cycles after the training window.
        # For very short histories, _prepare_temporal_validation explicitly falls
        # back to the original behavior because no honest holdout is possible.

        best_score = -float('inf')
        best_strat = BudgetStrategy.HYBRID_VOLATILITY
        best_config = StrategyConfig()

        # Grid definition
        grid = {'p': [75, 85], 'k': [1.05, 1.2], 'sigma_mult': [0.8, 1.0]}
        keys = list(grid.keys())
        combinations = [dict(zip(keys, v)) for v in itertools.product(*grid.values())]

        print("\n" + "🔮" * 15 + " WIZARD LEADERBOARD " + "🔮" * 15)
        print(f"{'STRATEGY':25} | {'SCORE':8} | {'BEST PARAMETERS'}")
        print("-" * 85)

        for strat in BudgetStrategy:
            strat_best_score = -float('inf')
            strat_best_config = StrategyConfig()

            for params in combinations:
                current_config = StrategyConfig(
                    percentile_target=params.get('p', 75),
                    safety_multiplier=params.get('k', 1.1),
                    volatility_sensitivity=params.get('sigma_mult', 0.8),
                    histogram_bins=params.get('bins', 10)
                )
                
                test_results = training_orchestrator.run_pipeline(strat, current_config)
                score = StrategyAutoTuner.evaluate(cycle_history, test_results)
                
                if score > strat_best_score:
                    strat_best_score = score
                    strat_best_config = current_config
                
                if score > best_score:
                    best_score = score
                    best_strat = strat
                    best_config = current_config

            print(f"{strat.name:25} | {strat_best_score:8} | {strat_best_config}")
        
        print("="*85 + f"\nOVERALL WINNER: {best_strat.name} | {best_config}\n" + "="*85)
        return best_strat, best_config

    @staticmethod
    def _prepare_temporal_validation(
        orchestrator: "Orchestrator",
    ) -> Tuple["Orchestrator", Dict[str, List[Tuple[str, float]]]]:
        """Fit on earlier cycles and reserve the most recent 20% for scoring."""
        cycle_names = sorted({
            item['cycle']
            for item in orchestrator.reporting_data
            if item['cycle'] != "Initial"
        })

        if len(cycle_names) < 2:
            return orchestrator, StrategyAutoTuner._build_cycle_history(orchestrator.reporting_data)

        holdout_size = max(1, math.ceil(len(cycle_names) * 0.2))
        validation_cycles = set(cycle_names[-holdout_size:])
        training_transactions = [
            transaction
            for transaction, item in zip(orchestrator.transactions, orchestrator.reporting_data)
            if item['cycle'] not in validation_cycles
        ]
        validation_data = [
            item
            for item in orchestrator.reporting_data
            if item['cycle'] in validation_cycles
        ]

        training_domain = BudgetDomain(
            transactions=training_transactions,
            category_cluster_map=orchestrator.domain.category_cluster_map,
            budget_overrides=orchestrator.domain.budget_overrides,
        )
        training_orchestrator = orchestrator.__class__(training_domain)
        return training_orchestrator, StrategyAutoTuner._build_cycle_history(validation_data)

    @staticmethod
    def _build_cycle_history(reporting_data) -> Dict[str, List[Tuple[str, float]]]:
        cycle_history = defaultdict(list)
        cat_cycle_map = defaultdict(lambda: defaultdict(float))

        for item in reporting_data:
            cat_cycle_map[item['category']][item['cycle']] += item['amount']

        for cat, cycles in cat_cycle_map.items():
            cycle_history[cat] = list(cycles.items())

        return dict(cycle_history)

    @staticmethod
    def evaluate(cycle_history: Dict[str, List[Tuple[str, float]]], processed_results: List[ProcessedCategory]) -> float:
        """
        Pure Python Evaluation Logic.
        Replaces the 'merge' and vectorized math with a targeted DTO loop.
        """
        score = 0.0
        categories_evaluated = 0
        
        # Filters: We ignore the same system clusters as before
        ignored_clusters = {'0. Incoming', '0. Internal', '1. Core'}
        
        # Create a lookup map for the processed results for O(1) access
        results_map = {p.category: p for p in processed_results}
        
        for cat, history_items in cycle_history.items():
            result = results_map.get(cat)
            
            # Skip if category wasn't processed or belongs to an ignored cluster
            if not result or result.master_cluster in ignored_clusters:
                continue
                
            if result.theoretical_budget <= 0:
                continue
            
            categories_evaluated += 1
            
            for _, actual_amount in history_items:
                # Calculate Ratio: Actual / Budget
                ratio = actual_amount / result.theoretical_budget
                
                # SCORING LOGIC (Exactly as before)
                # Success: Spending is between 80% and 102% of budget
                if 0.8 <= ratio <= 1.02:
                    score += 100
                
                # Penalty: Spending exceeded budget by more than 10%
                elif ratio > 1.1:
                    score -= 80
        
        return score if categories_evaluated > 0 else 0.0
