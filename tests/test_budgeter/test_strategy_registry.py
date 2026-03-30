import pytest
from budgeter.strategy_registry import StrategyRegistry
from model.models import CategoryStats, StrategyConfig
from config.config import BudgetStrategy

class TestStrategyRegistry:
    """
    Unit tests for the Strategy Engine.
    Enforces 100% branch coverage and strict 2-decimal equality.
    """

    @pytest.fixture
    def stats(self):
        # Median=100.0, Std=20.0 -> CV=0.2
        return CategoryStats(median=100.0, std=20.0, count=5, frequency=1.0)

    @pytest.fixture
    def cycle_data(self):
        # p75 is 110.0
        return [80, 90, 100, 110, 120]

    def test_percentile_guardrail(self, cycle_data, stats):
        # 110.0 * 1.1 = 121.0
        config = StrategyConfig(percentile_target=75, safety_multiplier=1.1)

        result = StrategyRegistry.compute_atomic(
            BudgetStrategy.PERCENTILE_GUARDRAIL, cycle_data, stats,config
        )
        assert result == 121.0

    def test_adaptive_z_score(self, cycle_data, stats):
        # 100.0 + (0.8 * 20.0) = 116.0
        config = StrategyConfig(volatility_sensitivity=0.8)
        result = StrategyRegistry.compute_atomic(
            BudgetStrategy.ADAPTIVE_Z_SCORE, cycle_data, stats, config
        )
        assert result == 116.0

    def test_variance_buffer(self, cycle_data, stats):
        # 100.0 + (0.8 * 20.0) = 116.0

        result = StrategyRegistry.compute_atomic(
            BudgetStrategy.VARIANCE_BUFFER, cycle_data, stats
        )
        assert result == 116.0

    def test_hybrid_volatility(self, cycle_data, stats):
        # CV is 0.2. 100.0 * (1 + 0.2) = 120.0
        result = StrategyRegistry.compute_atomic(
            BudgetStrategy.HYBRID_VOLATILITY, cycle_data, stats
        )
        assert result == 120.0

    def test_histogram_mode_logic(self, stats):
        # Peak at 200
        data = [10, 20, 195, 200, 205, 500]
        config = StrategyConfig(histogram_bins=3, safety_multiplier=1.0)
        result = StrategyRegistry.compute_atomic(
            BudgetStrategy.HISTOGRAM_MODE, data, stats, config
        )
        # Midpoint of the peak bin should be > 150
        assert result > 150

    def test_histogram_mode_with_single_point(self, stats):
        """
        Hits the 'if data.size < 2' branch inside HISTOGRAM_MODE.
        Ensures 100% coverage of the registry.
        """
        data = [100.0]
        result = StrategyRegistry.compute_atomic(
            BudgetStrategy.HISTOGRAM_MODE, data, stats
        )
        # Should return the median (100.0) from the stats DTO
        assert result == 100.0

    def test_empty_data_fallback(self, stats):
        # Should return median rounded
        assert StrategyRegistry.compute_atomic(BudgetStrategy.PERCENTILE_GUARDRAIL, [], stats) == 100.0

    def test_unhandled_strategy_fallback(self, cycle_data, stats):
        # Hits the 'else' branch
        assert StrategyRegistry.compute_atomic(BudgetStrategy.VOLATILITY_SHOCK_P90, cycle_data, stats) == 100.0

    def test_strict_rounding(self, stats):
        # 100 + (0.3333333 * 20) = 106.6666... -> 106.67
        config = StrategyConfig(volatility_sensitivity=0.3333333)
        result = StrategyRegistry.compute_atomic(
            BudgetStrategy.ADAPTIVE_Z_SCORE, [100], stats, config
        )
        assert result == 106.67