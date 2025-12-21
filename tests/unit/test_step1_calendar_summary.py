
from datetime import date

from bank_analysis.adapters.calendar_cycle import CalendarCycleGrouper
from bank_analysis.domain.entities import Transaction
from bank_analysis.domain.reporting import summary


def test_compute_monthly_summary_core_with_calendar_cycle_basic():
    txns = [
        # January
        Transaction(date_op=date(2025,1,25), month="2025-01", category="Salaire fixe", category_parent="Income",   amount=3700.0, message="DEFAULT MESSAGE"),
        Transaction(date_op=date(2025,1,10), month="2025-01", category="Groceries",    category_parent="Essentials",amount=-150.50, message="DEFAULT MESSAGE"),
        Transaction(date_op=date(2025,1,15), month="2025-01", category="Rent",         category_parent="Housing",   amount=-1200.0, message="DEFAULT MESSAGE"),
        Transaction(date_op=date(2025,1,31), month="2025-01", category="Internal debit",category_parent="Mouvements internes débiteurs",amount=-200.0, message="DEFAULT MESSAGE"),
        # February
        Transaction(date_op=date(2025,2,25), month="2025-02", category="Salaire fixe", category_parent="Income",    amount=3700.0, message="DEFAULT MESSAGE"),
        Transaction(date_op=date(2025,2,5),  month="2025-02", category="Transport",    category_parent="Essentials",amount=-90.0, message="DEFAULT MESSAGE"),
        Transaction(date_op=date(2025,2,10), month="2025-02", category="Dinner",       category_parent="Leisure",   amount=-65.0, message="DEFAULT MESSAGE"),
        Transaction(date_op=date(2025,2,15), month="2025-02", category="Internal credit",category_parent="Mouvements internes créditeurs",amount=-50.0, message="DEFAULT MESSAGE"),
    ]

    grouper = CalendarCycleGrouper()
    out = summary.compute_monthly_summary_core(txns, cycle_grouper=grouper)
    assert [r.month for r in out] == ["2025-01", "2025-02"]

    jan = out[0]
    jan_expenses = round(abs(-150.50 + -1200.0), 2)  # 1350.5
    assert jan.total_salary == 3700.0
    assert jan.total_expenses == jan_expenses
    assert jan.nb_expense_operations == 2
    assert jan.total_savings == round(3700.0 - jan_expenses, 2)
    assert jan.total_savings_vs_theoretical == round(3700.0 - jan_expenses, 2)  # default theoretical ref = 3700.0

    feb = out[1]
    feb_expenses = round(abs(-90.0 + -65.0), 2)  # 155.0
    assert feb.total_salary == 3700.0
    assert feb.total_expenses == feb_expenses
    assert feb.nb_expense_operations == 2
    assert feb.total_savings == round(3700.0 - feb_expenses, 2)
    assert feb.total_savings_vs_theoretical == round(3700.0 - feb_expenses, 2)

def test_groups_exist_even_if_only_one_side_present():
    # Only expenses, no salary
    txns_exp_only = [
        Transaction(date_op=date(2025,1,5), month="2025-01", category="Rent",      category_parent="Housing",   amount=-1000.0, message="DEFAULT MESSAGE"),
        Transaction(date_op=date(2025,1,3), month="2025-01", category="Groceries", category_parent="Essentials",amount=-50.0, message="DEFAULT MESSAGE"),
    ]
    grouper = CalendarCycleGrouper()
    out = summary.compute_monthly_summary_core(txns_exp_only, cycle_grouper=grouper)
    assert [r.month for r in out] == ["2025-01"]
    assert out[0].total_salary == 0.0
    assert out[0].total_expenses == 1050.0
    assert out[0].nb_expense_operations == 2

    # Only salary, no expenses
    txns_salary_only = [
        Transaction(date_op=date(2025,3,25), month="2025-03", category="Salaire fixe", category_parent="Income", amount=3700.0, message="DEFAULT MESSAGE"),
    ]
    out2 = summary.compute_monthly_summary_core(txns_salary_only, cycle_grouper=grouper)
    assert [r.month for r in out2] == ["2025-03"]
    assert out2[0].total_expenses == 0.0
    assert out2[0].nb_expense_operations == 0
