import pytest
from categorizer.categorizer import Categorizer
from model.models import CategoryStats, ClusterLabel

class TestCategorizer:
    """
    Unit tests for the Categorizer.
    Focuses on achieving 100% branch coverage and DTO contract validation.
    """

    @pytest.fixture
    def categorizer(self):
        # We test with both an Enum and a raw string in the mapping
        return Categorizer(mapping={
            "Netflix": ClusterLabel.OTHER_RECURRING,
            "Rent": "1. Core" 
        })

    def test_mapping_priority_enum(self, categorizer):
        """Ensures Enum-based mappings are correctly resolved to their value."""
        stats = CategoryStats(median=10, std=0, count=1, frequency=1.0)
        result = categorizer.classify("Netflix", stats, "Netflix", -15.99)
        assert result == "4. Other Recurring"

    def test_mapping_priority_string(self, categorizer):
        """Ensures string-based mappings work as a fallback."""
        stats = CategoryStats(median=10, std=0, count=1, frequency=1.0)
        result = categorizer.classify("Rent", stats, "Rent Payment", -800)
        assert result == "1. Core"

    def test_internal_keyword_detection(self, categorizer):
        """Ensures 'virement' keyword triggers the Internal cluster."""
        stats = CategoryStats(median=100, std=0, count=1, frequency=1.0)
        result = categorizer.classify("Savings", stats, "Virement vers Livret A", -100)
        assert result == ClusterLabel.INTERNAL.value

    def test_incoming_amount_detection(self, categorizer):
        """Ensures positive amounts are classified as Incoming."""
        stats = CategoryStats(median=2000, std=0, count=1, frequency=1.0)
        result = categorizer.classify("Salary", stats, "Paycheck", 2500.0)
        assert result == ClusterLabel.INCOMING.value

    @pytest.mark.parametrize("freq, cv, expected", [
        (0.8, 0.2, ClusterLabel.CORE.value),             # Stable & Frequent
        (0.8, 0.5, ClusterLabel.OTHER_RECURRING.value),   # Volatile & Frequent
        (0.5, 0.0, ClusterLabel.OTHER_PUNCTUAL.value),    # Occasional
        (0.05, 0.0, ClusterLabel.EXCEPTIONAL.value),      # Rare
    ])
    def test_statistical_logic(self, categorizer, freq, cv, expected):
        """Verify the threshold logic using the CategoryStats DTO."""
        stats = CategoryStats(median=100.0, std=cv*100.0, count=5, frequency=freq)
        # Using a generic label and negative amount to avoid earlier branch exits
        result = categorizer.classify("Utility", stats, "Electric Bill", -100.0)
        assert result == expected