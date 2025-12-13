
from datetime import date
from bank_analysis.domain.entities import Transaction
from bank_analysis.domain.reporting import summary
from bank_analysis.adapters.salary_cycle import SalaryCycleGrouper

def test_compute_monthly_summary_core_with_salary_cycle_two_periods_and_outside():
    txns = [
        # Salary anchors
        Transaction(date_op=date(2025,1,25), month="2025-01", category="Salaire fixe", category_parent="Income", amount=3700.0),
        Transaction(date_op=date(2025,2,25), month="2025-02", category="Salaire fixe", category_parent="Income", amount=3700.0),

        # Expenses between the anchors (count towards first period)
        Transaction(date_op=date(2025,2,5),  month="2025-02", category="Transport", category_parent="Essentials", amount=-90.0),
        Transaction(date_op=date(2025,2,10), month="2025-02", category="Dinner",    category_parent="Leisure",    amount=-65.0),

        # Expense before the first salary date -> “Outside salary periods”
        Transaction(date_op=date(2025,1,10), month="2025-01", category="Groceries", category_parent="Essentials", amount=-50.0),

        # Internal movement (excluded)
        Transaction(date_op=date(2025,1,31), month="2025-01", category="Internal debit", category_parent="Mouvements internes débiteurs", amount=-200.0),
    ]

    grouper = SalaryCycleGrouper(txns)
    out = summary.compute_monthly_summary_core(txns, cycle_grouper=grouper)

    # Expect 3 groups: first salary period, second salary period, and the "outside" bucket
    labels = [r.month for r in out]
    assert labels[0].startswith("2025-01-25 to 2025-02-24"), labels
    assert labels[1].startswith("2025-02-25 to"), labels
    assert labels[2] == "Outside salary periods", labels

    # First period: salary on Jan 25 + two Feb expenses (internal excluded)
    period1 = out[0]
    assert period1.total_salary == 3700.0
    assert period1.total_expenses == 155.0  # 90 + 65
    assert period1.nb_expense_operations == 2

    # Second period: salary on Feb 25, no expenses after
    period2 = out[1]
    assert period2.total_salary == 3700.0
    assert period2.total_expenses == 0.0
    assert period2.nb_expense_operations == 0

    # Outside salary periods: only the Jan 10 expense (internal excluded already)
    outside = out[2]
    assert outside.total_salary == 0.0
    assert outside.total_expenses == 50.0
    assert outside.nb_expense_operations == 1
