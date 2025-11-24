from typing import List, Sequence
import pandas as pd

from ..adapters.calendar_cycle import CalendarCycleGrouper
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
      return domain_analysis.compute_monthly_summary_core(txns,
                                                          cycle_grouper=self.cycle_grouper,
                                                          salary_category=self.salary_category,
                                                          exclude_parents=frozenset(self.exclude_parents),
                                                          ref_theoretical_salary=self.ref_salary,
                                                          )

