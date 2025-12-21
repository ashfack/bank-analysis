
from datetime import date
from bank_analysis.domain.entities import Transaction
from bank_analysis.usecases.compute_monthly_summary import ComputeMonthlySummaryUseCase
from bank_analysis.adapters.calendar_cycle import CalendarCycleGrouper
from bank_analysis.adapters.salary_cycle import SalaryCycleGrouper

def _sample_txns():
    return [
        # Salary anchors
        Transaction(date_op=date(2025,1,25), month="2025-01", category="Salaire fixe", category_parent="Income", amount=3700.0, message="DEFAULT MESSAGE"),
        Transaction(date_op=date(2025,2,25), month="2025-02", category="Salaire fixe", category_parent="Income", amount=3700.0, message="DEFAULT MESSAGE"),
        # Calendar-month expenses (also fall into first salary period)
        Transaction(date_op=date(2025,1,10), month="2025-01", category="Groceries", category_parent="Essentials", amount=-50.0, message="DEFAULT MESSAGE"),
        Transaction(date_op=date(2025,2,5),  month="2025-02", category="Transport", category_parent="Essentials", amount=-90.0, message="DEFAULT MESSAGE"),
        Transaction(date_op=date(2025,2,10), month="2025-02", category="Dinner",    category_parent="Leisure",    amount=-65.0, message="DEFAULT MESSAGE"),
        # Internal excluded
        Transaction(date_op=date(2025,1,31), month="2025-01", category="Internal debit", category_parent="Mouvements internes débiteurs", amount=-200.0, message="DEFAULT MESSAGE"),
    ]

def test_usecase_with_calendar_cycle():
    txns = _sample_txns()
    uc = ComputeMonthlySummaryUseCase(cycle_grouper=CalendarCycleGrouper())
    out = uc.execute(txns)

    # Calendar grouping: "2025-01", "2025-02"
    assert [r.month for r in out] == ["2025-01", "2025-02"]
    jan = out[0]
    assert jan.total_salary == 3700.0
    assert jan.total_expenses == 50.0
    feb = out[1]
    assert feb.total_salary == 3700.0
    assert feb.total_expenses == 155.0  # 90 + 65

def test_usecase_with_salary_cycle():
    txns = _sample_txns()
    uc = ComputeMonthlySummaryUseCase(cycle_grouper=SalaryCycleGrouper(txns))
    out = uc.execute(txns)

    labels = [r.month for r in out]
    assert labels[0].startswith("2025-01-25 to 2025-02-24")
    assert labels[1].startswith("2025-02-25 to")

    p1 = out[0]
    assert p1.total_salary == 3700.0
    assert p1.total_expenses == 155.0  # 90 + 65
    p2 = out[1]
    assert p2.total_salary == 3700.0
    assert p2.total_expenses == 0.0
