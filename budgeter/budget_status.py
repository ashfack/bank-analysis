from enum import Enum


class BudgetStatus(str, Enum):
    NEUTRAL = "neutral"
    DARK_GREEN = "dark_green"
    LIGHT_GREEN = "light_green"
    ORANGE = "orange"
    RED = "red"


def get_budget_status(value: float, limit: float, cluster: str) -> BudgetStatus:
    """Classify one budget cell consistently across every presentation."""
    if value == 0:
        return BudgetStatus.NEUTRAL

    if cluster.startswith("0."):
        return BudgetStatus.DARK_GREEN

    if value <= limit:
        return BudgetStatus.LIGHT_GREEN if value > limit * 0.5 else BudgetStatus.DARK_GREEN

    if value <= limit * 1.5:
        return BudgetStatus.ORANGE

    return BudgetStatus.RED
