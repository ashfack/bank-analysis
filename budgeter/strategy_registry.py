from typing import Callable, Dict, Hashable, Sequence

import numpy as np

from config.config import BudgetStrategy
from model.models import CategoryStats, StrategyConfig


StrategyCalculator = Callable[[np.ndarray, CategoryStats, StrategyConfig], float]


def _percentile_guardrail(
    data: np.ndarray, stats: CategoryStats, config: StrategyConfig
) -> float:
    return float(np.percentile(data, config.percentile_target)) * config.safety_multiplier


def _adaptive_z_score(
    data: np.ndarray, stats: CategoryStats, config: StrategyConfig
) -> float:
    return stats.median + config.volatility_sensitivity * stats.std


def _histogram_mode(
    data: np.ndarray, stats: CategoryStats, config: StrategyConfig
) -> float:
    if data.size < 2:
        return stats.median
    counts, bins = np.histogram(data, bins=config.histogram_bins)
    index = int(np.argmax(counts))
    midpoint = (bins[index] + bins[index + 1]) / 2
    return float(midpoint) * config.safety_multiplier


def _variance_buffer(
    data: np.ndarray, stats: CategoryStats, config: StrategyConfig
) -> float:
    return stats.median + 0.8 * stats.std


def _hybrid_volatility(
    data: np.ndarray, stats: CategoryStats, config: StrategyConfig
) -> float:
    return stats.median * (1.0 + min(stats.cv, 0.5))


class StrategyRegistry:
    """Resolve budget calculators without branching in the execution path."""

    _calculators: Dict[Hashable, StrategyCalculator] = {
        BudgetStrategy.PERCENTILE_GUARDRAIL: _percentile_guardrail,
        BudgetStrategy.ADAPTIVE_Z_SCORE: _adaptive_z_score,
        BudgetStrategy.HISTOGRAM_MODE: _histogram_mode,
        BudgetStrategy.VARIANCE_BUFFER: _variance_buffer,
        BudgetStrategy.HYBRID_VOLATILITY: _hybrid_volatility,
    }

    @classmethod
    def register(cls, strategy: Hashable, calculator: StrategyCalculator) -> None:
        cls._calculators[strategy] = calculator

    @classmethod
    def unregister(cls, strategy: Hashable) -> None:
        cls._calculators.pop(strategy, None)

    @classmethod
    def compute_atomic(
        cls,
        strategy: Hashable,
        cycle_data: Sequence[float],
        stats: CategoryStats,
        config: StrategyConfig | None = None,
    ) -> float:
        data = np.array(cycle_data)
        if data.size == 0:
            return round(float(stats.median), 2)

        calculator = cls._calculators.get(strategy)
        if calculator is None:
            raise ValueError(f"Unsupported budget strategy: {strategy!r}")

        result = calculator(data, stats, config or StrategyConfig())
        return round(float(result), 2)
