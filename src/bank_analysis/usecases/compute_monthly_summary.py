from typing import Sequence
from ..domain import analysis as domain_analysis
from ..domain.dto import MonthlySummaryRow
from ..domain.entities import Transaction
from ..ports.cycle_grouper import CycleGrouper


class ComputeMonthlySummaryUseCase:
    def __init__(self,
                 cycle_grouper: CycleGrouper,
                 salary_category: str = domain_analysis.SALARY_CATEGORY,
                 exclude_parents: set = domain_analysis.EXCLUDE_EXPENSE_PARENTS,
                 ref_salary: float = domain_analysis.REF_THEORETICAL_SALARY,

    ):
        self.salary_category = salary_category
        self.exclude_parents = exclude_parents
        self.ref_salary = ref_salary
        self.cycle_grouper = cycle_grouper

    def execute(self,
        txns: Sequence[Transaction]
    ) -> list[MonthlySummaryRow]:
      return domain_analysis.compute_monthly_summary_core(txns,
                                                          cycle_grouper=self.cycle_grouper,
                                                          salary_category=self.salary_category,
                                                          exclude_parents=frozenset(self.exclude_parents),
                                                          ref_theoretical_salary=self.ref_salary,
                                                          )

