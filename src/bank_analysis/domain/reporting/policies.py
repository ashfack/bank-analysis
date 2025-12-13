from dataclasses import dataclass
from typing import FrozenSet

@dataclass(frozen=True)
class BudgetPolicy:
    salary_category: str
    exclude_parents: FrozenSet[str]
    ref_theoretical_salary: float

DEFAULT_POLICY = BudgetPolicy(
    salary_category="Salaire fixe",
    exclude_parents=frozenset({"Mouvements internes débiteurs", "Mouvements internes créditeurs"}),
    ref_theoretical_salary=3700.0,
)
