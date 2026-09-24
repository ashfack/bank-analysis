from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from zipfile import ZipFile

from analysis_runner import run_uploaded_analysis


MAPPING = b"category;cluster\nSalaire fixe;0. Incoming\nExpense;2. Expense\n"
BUDGET = b"category;budget_override\n2. Expense;100\n"


def _bank_export(label: str, expense: str) -> bytes:
    return (
        "dateOp;label;amount;category\n"
        "2026-01-01;Salary;2000,00;Salaire fixe\n"
        f"2026-01-02;{label};-{expense};Expense\n"
    ).encode()


def _workbook_strings(report_bytes: bytes) -> str:
    with ZipFile(BytesIO(report_bytes)) as workbook:
        return workbook.read("xl/sharedStrings.xml").decode()


def test_uploaded_analyses_are_isolated_when_run_concurrently():
    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(
            run_uploaded_analysis,
            _bank_export("FIRST_USER", "10,00"),
            MAPPING,
            BUDGET,
        )
        second = executor.submit(
            run_uploaded_analysis,
            _bank_export("SECOND_USER", "20,00"),
            MAPPING,
            BUDGET,
        )

    first_result = first.result()
    second_result = second.result()

    assert "FIRST_USER" in _workbook_strings(first_result.report_bytes)
    assert "SECOND_USER" not in _workbook_strings(first_result.report_bytes)
    assert "SECOND_USER" in _workbook_strings(second_result.report_bytes)
    assert "FIRST_USER" not in _workbook_strings(second_result.report_bytes)
    assert first_result.report_bytes != second_result.report_bytes
    assert first_result.duplicate_transaction_count == 0
    assert second_result.duplicate_transaction_count == 0


def test_uploaded_analysis_reports_duplicate_transactions():
    duplicated_export = (
        "dateOp;label;amount;category\n"
        "2026-01-01;Salary;2000,00;Salaire fixe\n"
        "2026-01-02;Repeated;-10,00;Expense\n"
        "2026-01-02;Repeated;-10,00;Expense\n"
    ).encode()

    result = run_uploaded_analysis(duplicated_export, MAPPING, BUDGET)

    assert result.duplicate_transaction_count == 1
