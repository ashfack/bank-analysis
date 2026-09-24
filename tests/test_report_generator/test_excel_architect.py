import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from model.models import BudgetView, EnrichedTransaction, ProcessedCategory
from report_generator.excel_architect import ExcelArchitect

class TestExcelArchitect:

    @pytest.fixture
    def sample_data(self):
        """Creates the results needed for the styling logic."""
        results = [
            ProcessedCategory("Rent", "0. Fixed", 1000, 0, 1, 1.0, 1000, 1000, 1000),
            ProcessedCategory("Water", "1. Bills", 100, 0, 1, 1.0, 100, 100, 40),
            ProcessedCategory("Ghost", "6. NoTarget", 100, 0, 1, 1.0, 100, 100, 50)
        ]
        return [], results

    @patch("pandas.ExcelWriter")
    def test_full_coverage_generate(self, mock_writer_class, sample_data):
        _, results = sample_data
        # Init with 1 argument as per your class source
        architect = ExcelArchitect("dummy.xlsx")
    
        # Setup Mock Infrastructure
        mock_writer_instance = MagicMock()
        mock_writer_class.return_value.__enter__.return_value = mock_writer_instance
    
        mock_sheets = {
            '📑 Pilotage': MagicMock(),
            '🔍 AI Mapping': MagicMock(),
            '📝 Ledger': MagicMock()
        }
        mock_writer_instance.sheets = mock_sheets
        mock_writer_instance.book = MagicMock()
        
        # --- FIX: Mock BudgetView with real numeric returns ---
        mock_view = MagicMock(spec=BudgetView)
        mock_view.cycles = ['C1']
        mock_view.clusters = ['0. Fixed', '1. Bills']
        mock_view.processed_categories = results
        
        # Define what get_amount and get_budget return to avoid Mock > Int errors
        def mock_get_amount(cycle, cluster):
            return 1000.0 if "Fixed" in cluster else 40.0
        
        def mock_get_budget(cluster):
            return 1000.0
            
        mock_view.get_amount.side_effect = mock_get_amount
        mock_view.get_budget.side_effect = mock_get_budget
    
        # Raw transactions for the ledger
        enriched_mock = [
            EnrichedTransaction(
                category='Rent',
                amount=1000.0,
                raw_amount=-1000.0,
                label='Home payment',
                cycle='C1',
            )
        ]

        with patch("pandas.DataFrame.to_excel"):
            architect.generate(mock_view, enriched_mock)
    
        # Verify it attempted to write data
        pilotage = mock_sheets['📑 Pilotage']
        assert pilotage.write_number.called or pilotage.write_url.called

    def test_named_range_math_precision(self, sample_data):
        mock_wb = MagicMock()
        architect = ExcelArchitect("test.xlsx")
        data = pd.DataFrame([{'cycle': 'C1', 'master_cluster': '7. Insurance', 'amount': 100}])
        
        architect._create_named_ranges(mock_wb, data, "Details", "DTL", 10, ['cycle', 'master_cluster'])
        assert mock_wb.define_name.called

    def test_determine_color_branches(self, sample_data):
        arch = ExcelArchitect("test.xlsx")
        styles = arch._get_styles(MagicMock())

        # Test logic with real numbers
        assert arch._determine_color(120, 100, "Variable", styles) == styles['orange']
        assert arch._determine_color(40, 100, "Variable", styles) == styles['dark_green']
        assert arch._determine_color(0, 100, "Variable", styles) == styles['neutral']
