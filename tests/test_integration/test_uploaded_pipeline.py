from io import BytesIO
from zipfile import ZipFile

import pytest

from analysis_runner import run_uploaded_analysis


BANK_EXPORT = (
    "dateOp;label;amount;category\n"
    "2026-01-01;Monthly income;2000,00;Salaire fixe\n"
    "2026-01-02;Home payment;-800,00;Housing\n"
    "2026-01-03;Repeated purchase;-10,00;Unmapped expense\n"
    "2026-01-03;Repeated purchase;-10,00;Unmapped expense\n"
).encode()

MAPPING_CONFIG = (
    "category;cluster\n"
    "Salaire fixe;0. Incoming\n"
    "Housing;1. Core\n"
).encode()

BUDGET_CONFIG = (
    "category;budget_override\n"
    "0. Incoming;2000\n"
    "1. Core;900\n"
    "Unused cluster;100\n"
).encode()


def test_uploaded_files_flow_through_quality_analysis_and_excel_report():
    result = run_uploaded_analysis(
        BANK_EXPORT,
        MAPPING_CONFIG,
        BUDGET_CONFIG,
    )

    assert result.duplicate_transaction_count == 1
    assert result.auto_classified_categories == ("Unmapped expense",)
    assert result.unused_budget_targets == ("Unused cluster",)

    assert len(result.reporting_data) == 4
    assert result.view.get_amount("Cycle_du_2026-01-01", "0. Incoming") == 2000
    assert result.view.get_amount("Cycle_du_2026-01-01", "1. Core") == 820
    assert result.view.get_budget("0. Incoming") == pytest.approx(2000)
    assert result.view.get_budget("1. Core") == pytest.approx(900)

    with ZipFile(BytesIO(result.report_bytes)) as workbook:
        assert workbook.testzip() is None
        assert "xl/workbook.xml" in workbook.namelist()
        assert "xl/worksheets/sheet1.xml" in workbook.namelist()
