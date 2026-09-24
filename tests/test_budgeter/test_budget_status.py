import pytest

from budgeter.budget_status import BudgetStatus, get_budget_status


@pytest.mark.parametrize(
    ("value", "limit", "cluster", "expected"),
    [
        (0, 100, "2. Food", BudgetStatus.NEUTRAL),
        (200, 100, "0. Incoming", BudgetStatus.DARK_GREEN),
        (40, 100, "2. Food", BudgetStatus.DARK_GREEN),
        (80, 100, "2. Food", BudgetStatus.LIGHT_GREEN),
        (120, 100, "2. Food", BudgetStatus.ORANGE),
        (160, 100, "2. Food", BudgetStatus.RED),
        (120, 100, "10. Carburant", BudgetStatus.ORANGE),
    ],
)
def test_budget_status(value, limit, cluster, expected):
    assert get_budget_status(value, limit, cluster) == expected
