from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class Transaction:
    date_op: date             # "YYYY-MM-DD"
    month: str                 # "YYYY-MM"
    category: str
    category_parent: str
    amount: float              # negative => expense; positive => income
    message: str
    supplier: str =""
