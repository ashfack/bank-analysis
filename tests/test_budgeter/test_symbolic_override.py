import pytest
from budgeter.budget_custom_overrider import SymbolicOverride

class TestSymbolicOverride:
    """
    Ensures that the symbolic rule parsing logic is robust and handles 
    all edge cases as defined in the current implementation.
    """

    @pytest.mark.parametrize("rule, base_val, expected", [
        ("10%", 100, 10),      # Absolute ratio
        ("+10%", 100, 110),    # Incremental increase
        ("-10%", 100, 90),     # Incremental decrease
        ("+50", 100, 150),     # Additive increase
        ("-20", 100, 80),      # Additive decrease
        ("500", 100, 500),     # Hard override
        ("nan", 100, 100),     # Empty/NaN case
        (None, 100, 100),      # Null case
        ("invalid", 100, 100), # Non-numeric garbage
    ])
    def test_apply_logic(self, rule, base_val, expected):
        """Validates that rules are parsed and applied correctly to base values."""
        assert SymbolicOverride.apply(rule, base_val) == expected

    def test_precision_handling(self):
        """Ensures floating point strings are handled."""
        assert SymbolicOverride.apply("12.5%", 1000) == 125.0