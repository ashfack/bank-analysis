import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from model.models import ProcessedCategory, Transaction
import report_generator
from report_generator.excel_architect import ExcelArchitect

class TestExcelArchitect:

    @pytest.fixture
    def sample_data(self):
        """Creates the mapping and results needed for the styling logic."""
        results = [
            # 1. Trigger for '0.' cluster (Special styling)
            ProcessedCategory("Rent", "0. Fixed", 1000, 0, 1, 1.0, 1000, 1000, 1000),
            # 2. Trigger for 'Under 50%' (Dark Green)
            ProcessedCategory("Water", "1. Bills", 100, 0, 1, 1.0, 100, 100, 40),
            # 3. Trigger for '50% to 100%' (Light Green)
            ProcessedCategory("Gas", "2. Energy", 100, 0, 1, 1.0, 100, 100, 80),
            # 4. Trigger for '100% to 150%' (Orange)
            ProcessedCategory("Fun", "3. Leisure", 100, 0, 1, 1.0, 100, 100, 120),
            # 5. Trigger for '> 150%' (Red)
            ProcessedCategory("Gambling", "4. Risk", 100, 0, 1, 1.0, 100, 100, 200),
            # 6. Trigger for 'Neutral' (0 spending)
            ProcessedCategory("Savings", "5. Goal", 100, 0, 0, 0.0, 100, 100, 0),
            # A category with a budget but 0 actual spending
            ProcessedCategory("Buffer", "6. Extra", 100, 0, 0, 0.0, 100, 100, 0.0),
            # Path: The 100% coverage 'else' branch (val > 0 but NO target link)
            ProcessedCategory("Ghost", "6. NoTarget", 100, 0, 1, 1.0, 100, 100, 50)
        ]
        # Empty transactions are fine as init just converts them to a DF
        return [], results

    @pytest.fixture
    def enriched_mock(self):
        """Data designed to hit every single branch in _apply_styles."""
        return [
            {'category': 'Rent', 'amount': 1000.0, 'cycle': 'C1', 'dateOperation': pd.Timestamp('2026-01-01')},
            {'category': 'Water', 'amount': 40.0, 'cycle': 'C1', 'dateOperation': pd.Timestamp('2026-01-01')},
            {'category': 'Gas', 'amount': 80.0, 'cycle': 'C1', 'dateOperation': pd.Timestamp('2026-01-01')},
            {'category': 'Fun', 'amount': 120.0, 'cycle': 'C1', 'dateOperation': pd.Timestamp('2026-01-01')},
            {'category': 'Gambling', 'amount': 200.0, 'cycle': 'C1', 'dateOperation': pd.Timestamp('2026-01-01')},
            {'category': 'Ghost', 'amount': 50.0, 'cycle': 'C1', 'dateOperation': pd.Timestamp('2026-01-01')},
            # Note: Savings is omitted here to trigger the 'val == 0' / 'neutral' branch
        ]

    @patch("pandas.ExcelWriter")
    def test_full_coverage_generate(self, mock_writer_class, sample_data, enriched_mock):
        transactions, results = sample_data
        architect = ExcelArchitect(transactions, results, "dummy.xlsx")
    
        # Setup Mock Infrastructure
        mock_writer_instance = MagicMock()
        mock_writer_class.return_value.__enter__.return_value = mock_writer_instance
    
        # Pre-fill sheets with names that match the class logic EXACTLY
        mock_sheets = {
            'Pilotage': MagicMock(),
            'Mapping': MagicMock(),   # Changed from 'Categories Map'
            'Details': MagicMock()    # Changed from 'Transactions Detail'
        }
        mock_writer_instance.sheets = mock_sheets
        mock_writer_instance.book = MagicMock()
    
        # Execute generate
        with patch("pandas.DataFrame.to_excel"):
            architect.generate(enriched_mock)
    
        # Verifications
        # Note: If cells are clickable, write_url is called. If not, write_number is called.
        # To be safe, check if EITHER was called to confirm the loop ran.
        pilotage = mock_sheets['Pilotage']
        assert pilotage.write_number.called or pilotage.write_url.called



    def test_named_range_math_precision(self, sample_data):
    
        print("Hi")
        print(f"DEBUG: Importing from -> {report_generator.__file__}")
        transactions, results = sample_data
        data = pd.DataFrame([
            {'cycle': 'C1', 'master_cluster': '7. Insurance', 'amount': 100},
            {'cycle': 'C1', 'master_cluster': '9. Cash', 'amount': 50}
        ])
        
        mock_wb = MagicMock()
        architect = ExcelArchitect([], [], "test.xlsx")
        
        # Start at row 2486
        architect._create_named_ranges(mock_wb, data, "Details", "DTL", 2486, ['cycle', 'master_cluster'])
        
        calls = mock_wb.define_name.call_args_list
        
        # Check Cluster 7 (First call)
        name_7, range_7 = calls[0][0]
        # We check for $A$2486 (Start) and $G$2486 (End)
        assert "$A$2486" in range_7
        assert "$G$2486" in range_7
        assert "2487" not in range_7 # Ensure no overlap!

        # Check Cluster 9 (Second call)
        name_9, range_9 = calls[1][0]
        assert "$A$2487" in range_9
        assert "$G$2487" in range_9

    def test_prepare_summary_fallback(self, sample_data):
        from model.models import Transaction
        # Added 'label' to fix the TypeError
        tx = Transaction(amount=100, category="Rent", dateOperation="2026-01-01", label="Monthly Rent")
        
        _, results = sample_data
        # Pass the transaction list here!
        arch = ExcelArchitect([tx], results, "test.xlsx")
        
        summary = arch._prepare_summary([])
        
        assert 'cycle' in summary.columns
        assert summary['cycle'].iloc[0] == 'Unknown'

    def test_determine_color_branches(self, sample_data):
        transactions, results = sample_data
        arch = ExcelArchitect(transactions, results, "test.xlsx")
        styles = arch._get_excel_styles(MagicMock())

        # Test 'Orange' (> 100% and <= 150%)
        assert arch._determine_color(120, 100, "Variable", styles) == styles['orange']
        
        # Test 'Dark Green' (<= 50% of budget)
        assert arch._determine_color(40, 100, "Variable", styles) == styles['dark_green']
        
        # Test 'Neutral' (Spending is 0)
        assert arch._determine_color(0, 100, "Variable", styles) == styles['neutral']