import pandas as pd
from typing import List
from ..domain import analysis as domain_analysis
from ..domain.dto import CategoryBreakdownRow

class ComputeCategoryBreakdownUseCase:
    def __init__(self, exclude_parents: set = domain_analysis.EXCLUDE_EXPENSE_PARENTS):
        self.exclude_parents = exclude_parents

    def execute(self, df: pd.DataFrame) -> List[CategoryBreakdownRow]:
        if df is None or df.empty:
            raise ValueError("DataFrame is empty or None. Cannot compute category breakdown.")
        return domain_analysis.compute_category_breakdown(df, self.exclude_parents)
