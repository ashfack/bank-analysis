from typing import List, Sequence
import pandas as pd

from ..adapters.calendar_cycle import CalendarCycleGrouper
from ..domain import analysis as domain_analysis
from ..domain.dto import MonthlySummaryRow
from ..domain.entities import Transaction


class ComputeMonthlySummaryUseCase:
    def __init__(self,
                 salary_category: str = domain_analysis.SALARY_CATEGORY,
                 exclude_parents: set = domain_analysis.EXCLUDE_EXPENSE_PARENTS,
                 ref_salary: float = domain_analysis.REF_THEORETICAL_SALARY,
                 cycle: str = "calendar"
    ):
        self.salary_category = salary_category
        self.exclude_parents = exclude_parents
        self.ref_salary = ref_salary
        self.cycle = cycle

    def execute(self, df: pd.DataFrame, cycle: str = "calendar") -> List[MonthlySummaryRow]:
        if df is None or df.empty:
            raise ValueError("DataFrame is empty or None. Cannot compute monthly summary.")
        if cycle not in ("calendar", "salary"):
            raise ValueError(f"Invalid cycle: {cycle}")
        return domain_analysis.compute_monthly_summary(
            df,
            salary_category=self.salary_category,
            exclude_parents=self.exclude_parents,
            ref_theoretical_salary=self.ref_salary,
            cycle=cycle,
        )

    def execute_bis(self,
        txns: Sequence[Transaction]
    ) -> list[MonthlySummaryRow]:
      """
      Application use case that wires the domain service with the cycle strategy.
      Step 1: supports only 'calendar'. Step 2 will add 'salary'.
      """
      if self.cycle != "calendar":
        raise NotImplementedError(
          "Only 'calendar' cycle is supported in Step 1.")
      cycle_grouper = CalendarCycleGrouper()
      return domain_analysis.compute_monthly_summary_core(txns,
                                                          cycle_grouper=cycle_grouper,
                                                          salary_category=self.salary_category,
                                                          exclude_parents=frozenset(self.exclude_parents),
                                                          ref_theoretical_salary=self.ref_salary,
                                                          )

