from collections import defaultdict
from typing import Sequence

from bank_analysis.domain.entities import Transaction
from bank_analysis.domain.reporting.policies import BudgetPolicy, DEFAULT_POLICY
from bank_analysis.domain.value_objects import MonthlySummary
from bank_analysis.ports.cycle_grouper import CycleGrouper


def compute_monthly_summary_core(
    txns: Sequence[Transaction],
    cycle_grouper: CycleGrouper,
    policy: BudgetPolicy = DEFAULT_POLICY,
) -> list[MonthlySummary]:
  """
  Pure domain computation. Groups using the provided CycleGrouper.
  """
  salaries: dict[str, float] = defaultdict(float)
  expenses: dict[str, float] = defaultdict(float)
  ops_count: dict[str, int] = defaultdict(int)

  for t in txns:
    label = cycle_grouper.label_for_date(t.date_op)
    if t.category == policy.salary_category:
      salaries[label] += float(t.amount)
    if t.amount < 0 and t.category_parent not in policy.exclude_parents:
      expenses[label] += float(t.amount)  # negative sum
      ops_count[label] += 1

  groups = sorted(set(salaries) | set(expenses))
  out: list[MonthlySummary] = []
  for g in groups:
    total_salary = round(salaries.get(g, 0.0), 2)
    total_expenses = round(abs(expenses.get(g, 0.0)), 2)  # abs of negative sum
    nb_ops = ops_count.get(g, 0)

    total_savings = round(total_salary - total_expenses, 2)
    total_vs_theoretical = round(policy.ref_theoretical_salary - total_expenses, 2)

    out.append(MonthlySummary(
        month=g,
        total_salary=total_salary,
        total_expenses=total_expenses,
        nb_expense_operations=nb_ops,
        total_savings=total_savings,
        total_savings_vs_theoretical=total_vs_theoretical,
    ))
  return out