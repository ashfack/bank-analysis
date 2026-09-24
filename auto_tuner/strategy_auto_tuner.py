import itertools
import math
from dataclasses import dataclass
from typing import Tuple, List, Dict
from collections import defaultdict

from config.config import ACTIVE_STRATEGY, MANUAL_MODE, MANUAL_PARAMS, BudgetStrategy
from model.models import BudgetDomain, StrategyConfig, ProcessedCategory
# Note: Using Type Hinting for Orchestrator to avoid circular imports if necessary
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from orchestrator import Orchestrator

@dataclass(frozen=True)
class TuningSettings:
    manual_mode: bool = MANUAL_MODE
    active_strategy: BudgetStrategy = ACTIVE_STRATEGY
    manual_params: StrategyConfig = MANUAL_PARAMS
    percentile_targets: Tuple[int, ...] = (75, 85)
    safety_multipliers: Tuple[float, ...] = (1.05, 1.2)
    volatility_sensitivities: Tuple[float, ...] = (0.8, 1.0)


@dataclass(frozen=True)
class StrategyScore:
    strategy: BudgetStrategy
    score: float
    config: StrategyConfig


@dataclass(frozen=True)
class TuningResult:
    strategy: BudgetStrategy
    config: StrategyConfig
    leaderboard: Tuple[StrategyScore, ...]


class StrategyAutoTuner:
    """Responsibility: Discovery with detailed Parameter Leaderboard (Pure Python)"""

    def __init__(self, settings: TuningSettings | None = None):
        self.settings = settings or TuningSettings()

    def discover(self, orchestrator: "Orchestrator") -> TuningResult:
        if self.settings.manual_mode:
            return TuningResult(
                self.settings.active_strategy,
                self.settings.manual_params,
                (),
            )

        training_orchestrator, cycle_history = StrategyAutoTuner._prepare_temporal_validation(orchestrator)

        # Historical ground truth contains only cycles after the training window.
        # For very short histories, _prepare_temporal_validation explicitly falls
        # back to the original behavior because no honest holdout is possible.

        best_score = -float('inf')
        best_strat = BudgetStrategy.HYBRID_VOLATILITY
        best_config = StrategyConfig()

        combinations = itertools.product(
            self.settings.percentile_targets,
            self.settings.safety_multipliers,
            self.settings.volatility_sensitivities,
        )
        configurations = [
            StrategyConfig(
                percentile_target=percentile,
                safety_multiplier=multiplier,
                volatility_sensitivity=volatility,
            )
            for percentile, multiplier, volatility in combinations
        ]
        leaderboard = []

        for strat in BudgetStrategy:
            strat_best_score = -float('inf')
            strat_best_config = StrategyConfig()

            for current_config in configurations:
                test_results = training_orchestrator.run_pipeline(strat, current_config)
                score = StrategyAutoTuner.evaluate(cycle_history, test_results)
                
                if score > strat_best_score:
                    strat_best_score = score
                    strat_best_config = current_config
                
                if score > best_score:
                    best_score = score
                    best_strat = strat
                    best_config = current_config

            leaderboard.append(StrategyScore(strat, strat_best_score, strat_best_config))

        return TuningResult(best_strat, best_config, tuple(leaderboard))

    @staticmethod
    def _prepare_temporal_validation(
        orchestrator: "Orchestrator",
    ) -> Tuple["Orchestrator", Dict[str, List[Tuple[str, float]]]]:
        """Fit on earlier cycles and reserve the most recent 20% for scoring."""
        cycle_names = sorted({
            item.cycle
            for item in orchestrator.reporting_data
            if item.cycle != "Initial"
        })

        if len(cycle_names) < 2:
            return orchestrator, StrategyAutoTuner._build_cycle_history(orchestrator.reporting_data)

        holdout_size = max(1, math.ceil(len(cycle_names) * 0.2))
        validation_cycles = set(cycle_names[-holdout_size:])
        training_transactions = [
            transaction
            for transaction, item in zip(orchestrator.transactions, orchestrator.reporting_data)
            if item.cycle not in validation_cycles
        ]
        validation_data = [
            item
            for item in orchestrator.reporting_data
            if item.cycle in validation_cycles
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
            cat_cycle_map[item.category][item.cycle] += item.amount

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
