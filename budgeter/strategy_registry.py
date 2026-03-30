from typing import Sequence
import numpy as np
from config.config import BudgetStrategy
from model.models import CategoryStats, StrategyConfig

class StrategyRegistry:
    @staticmethod
    def compute_atomic(strategy: BudgetStrategy, 
                       cycle_data: Sequence[float], 
                       stats: CategoryStats, 
                       config: StrategyConfig=None) -> float:
        data = np.array(cycle_data)

        if config is None:
            config = StrategyConfig()
        
        if data.size == 0:
            return round(float(stats.median), 2)

        if strategy == BudgetStrategy.PERCENTILE_GUARDRAIL:
            # Target the specific percentile and apply the buffer
            base_val = np.percentile(data, config.percentile_target)
            result = base_val * config.safety_multiplier
            
        elif strategy == BudgetStrategy.ADAPTIVE_Z_SCORE:
            # Median + (Volatility Sensitivity * Standard Deviation)
            result = stats.median + (config.volatility_sensitivity * stats.std)
            
        elif strategy == BudgetStrategy.HISTOGRAM_MODE:
            if data.size < 2: 
                result = stats.median
            else:
                counts, bins = np.histogram(data, bins=config.histogram_bins)
                idx = np.argmax(counts)
                mode_midpoint = (bins[idx] + bins[idx+1]) / 2
                result = mode_midpoint * config.safety_multiplier
        
        elif strategy == BudgetStrategy.VARIANCE_BUFFER:
            # Uses a hardcoded 0.8 sensitivity as per business rules
            result = stats.median + (0.8 * stats.std)

        elif strategy == BudgetStrategy.HYBRID_VOLATILITY:
            # Uses the Coefficient of Variation (CV) to scale the median
            # Caps the impact at +50% to prevent outliers from exploding the budget
            impact_factor = min(stats.cv, 0.5)
            result = stats.median * (1.0 + impact_factor)
            
        else:
            result = stats.median

        return round(float(result), 2)