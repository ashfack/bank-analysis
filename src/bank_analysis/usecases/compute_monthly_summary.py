from typing import List
import pandas as pd
from ..domain import analysis as domain_analysis
from ..domain.dto import MonthlySummaryRow

class ComputeMonthlySummaryUseCase:
    def __init__(self,
                 salary_category: str = domain_analysis.SALARY_CATEGORY,
                 exclude_parents: set = domain_analysis.EXCLUDE_EXPENSE_PARENTS,
                 ref_salary: float = domain_analysis.REF_THEORETICAL_SALARY):
        self.salary_category = salary_category
        self.exclude_parents = exclude_parents
        self.ref_salary = ref_salary

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
