from unittest.mock import patch

import pytest
import pandas as pd
from io import StringIO
from loader.data_loader import DataLoader
from model.models import Transaction
from config.config import (
    COL_RAW_DATE, COL_RAW_AMOUNT, COL_RAW_CATEGORY, DOMAIN_DATE
)

class TestDataLoader:

    @pytest.fixture
    def raw_csv_content(self):
        """Simulates a messy European CSV from a bank."""
        # Using ; as separator, spaces/xa0 in numbers, and commas for decimals
        return (
            f"{COL_RAW_DATE};{COL_RAW_AMOUNT};{COL_RAW_CATEGORY};label\n"
            "2026-01-01;1 250,50;Rent;Apartment Jan\n"
            "2026-01-05;45,99;Food;Starbucks\n"
            "2026-01-03;10,00;Hobby;Steam\n"
        )

    @pytest.fixture
    def override_content(self):
        """Simulates an override file with comments and empty lines."""
        return (
            "# Manual Adjustments\n"
            f"{COL_RAW_CATEGORY};budget_override\n"
            "Rent;1250\n"
            "\n"
            "# Temporary boost\n"
            "Food;+10%\n"
        )

    # --- 1. Testing Transaction Preparation ---

    def test_prepare_transaction_data_cleaning(self, tmp_path, raw_csv_content):
        """Ensures European strings are converted to clean Transaction objects."""
        path = tmp_path / "transactions.csv"
        path.write_text(raw_csv_content, encoding='utf-8')

        transactions = DataLoader.prepare_transaction_data(str(path))

        assert len(transactions) == 3
        assert isinstance(transactions[0], Transaction)
        
        # Verify European numeric cleaning (1 250,50 -> 1250.5)
        # Note: Index 0 is '2026-01-01' because we sort by date
        assert transactions[0].amount == 1250.5
        assert transactions[0].category == "Rent"
        assert transactions[0].label == "Apartment Jan"

    def test_prepare_transaction_data_sorting(self, tmp_path, raw_csv_content):
        """Ensures the Loader returns transactions sorted by dateOperation."""
        path = tmp_path / "transactions.csv"
        path.write_text(raw_csv_content, encoding='utf-8')

        transactions = DataLoader.prepare_transaction_data(str(path))

        # Original order was Jan 1, Jan 5, Jan 3. 
        # Sorted should be Jan 1, Jan 3, Jan 5.
        assert transactions[0].dateOperation < transactions[1].dateOperation
        assert transactions[1].dateOperation < transactions[2].dateOperation
        assert transactions[1].label == "Steam" # Jan 3rd

    def test_prepare_transaction_data_missing_cols(self, tmp_path):
        """Ensures an immediate crash if critical columns are missing."""
        path = tmp_path / "bad_data.csv"
        path.write_text("wrong_col;another_col\n1;2", encoding='utf-8')

        with pytest.raises(ValueError, match="missing required columns"):
            DataLoader.prepare_transaction_data(str(path))

    # --- 2. Testing Mapping & Overrides ---

    def test_load_category_cluster_map(self, tmp_path):
        path = tmp_path / "map.csv"
        path.write_text("category;cluster\nRent;Fixed\nFood;Lifestyle", encoding='utf-8')

        mapping = DataLoader.load_category_cluster_map(str(path))
        assert mapping == {"Rent": "Fixed", "Food": "Lifestyle"}

    def test_load_budget_overrides_with_comments(self, tmp_path, override_content):
        """Ensures the parser ignores # comments and empty lines."""
        path = tmp_path / "overrides.csv"
        path.write_text(override_content, encoding='utf-8')

        overrides = DataLoader.load_budget_overrides(str(path))
        
        assert len(overrides) == 2
        assert overrides["Rent"] == "1250"
        assert overrides["Food"] == "+10%"
        assert "# Manual Adjustments" not in overrides

    # --- 3. Testing Resilience ---

    def test_missing_files_returns_empty(self):
        """Graceful fallback for non-essential files."""
        assert DataLoader.load_category_cluster_map("ghost.csv") == {}
        assert DataLoader.load_budget_overrides("ghost.csv") == {}

    def test_prepare_data_file_not_found(self):
        """Essential files should raise a FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            DataLoader.prepare_transaction_data("critical_missing.csv")

    # --- FIX FOR LINE 22: Wrong Mapping Headers ---
    def test_load_mapping_wrong_headers(self, tmp_path):
        """Triggers line 22: File exists but headers are wrong."""
        path = tmp_path / "wrong_headers.csv"
        # Using wrong column names
        path.write_text("wrong_col;another_wrong_col\nValue1;Value2", encoding='utf-8')
        
        mapping = DataLoader.load_category_cluster_map(str(path))
        assert mapping == {} # Should return empty because headers don't match

    # --- FIX FOR LINE 42: Catastrophic Exception ---
    def test_load_overrides_catastrophic_error(self, tmp_path):
        """Triggers line 42: Force a real Exception during parsing."""
        path = tmp_path / "broken.csv"
        path.write_text("category;budget_override\nValue;100", encoding='utf-8')
        
        # We mock pd.read_csv to throw an error when it touches this specific method
        with patch("pandas.read_csv", side_effect=Exception("Catastrophic Failure")):
            result = DataLoader.load_budget_overrides(str(path))
            assert result == {} # Should catch the exception and return empty dict

    def test_prepare_transaction_data_preserves_negative_european_amounts(self, tmp_path):
        """
        Regression Test: Ensures that French-formatted negative amounts 
        (e.g., '-1 250,50') are correctly converted to -1250.50.
        """
        path = tmp_path / "negative_test.csv"
        # Note the non-breaking space (\xa0) and the comma
        content = (
            "dateOp;label;amount;category\n"
            "2026-01-01;Supermarket;-1\xa0250,50;Alimentation\n"
            "2026-01-02;Salary;3000,00;Salaire fixe"
        )
        path.write_text(content, encoding='utf-8')

        transactions = DataLoader.prepare_transaction_data(str(path))
        
        # Check the Supermarket transaction
        supermarket = next(t for t in transactions if t.label == "Supermarket")
        
        # CRITICAL ASSERTION: 
        # If the loader is broken, this will be 1250.5 or 250.5
        assert supermarket.amount == -1250.50, f"Expected -1250.50, got {supermarket.amount}"