
# src/bank_analysis/domain/reporting/category_rules.py
from dataclasses import dataclass
from typing import FrozenSet, Pattern, Tuple
import re

@dataclass(frozen=True)
class SupplierPattern:
    """
    Supplier detection rule based on 'supplier_found' (regex, case-insensitive).
    - name: display label used in the breakdown (e.g., 'Leclerc')
    - regex: compiled pattern applied to supplier_found (case-insensitive)
    """
    name: str
    regex: Pattern[str]


@dataclass(frozen=True)
class CategoryRules:
    """
    Business rules for transaction classification:
      - mandatory_categories: exact match (case-insensitive) on 'category'
      - salary_category: exact label for fixed salary (e.g., 'Salaire fixe')
      - reimbursement_keywords: substrings (case-insensitive) searched in 'category'
      - supplier_patterns: patterns applied to 'supplier_found' (case-insensitive)
    """
    mandatory_categories: FrozenSet[str]
    salary_category: str
    reimbursement_keywords: FrozenSet[str]
    supplier_patterns: Tuple[SupplierPattern, ...]


# Default rules based on your specification
DEFAULT_CATEGORY_RULES = CategoryRules(
    mandatory_categories=frozenset({
        "Loyers, charges",
        "Transports quotidiens (métro, bus...)",
        "Energie (électricité, gaz, fuel, chauffage...)",
        "Impôts & taxes",
        "Téléphonie (fixe et mobile)",
        "Multimedia à domicile (tv, internet, téléphonie...)",
        "Complémentaires santé",
    }),
    salary_category="Salaire fixe",
    reimbursement_keywords=frozenset({
        "remboursement",
        "remboursements",
        "remboursement de frais",
    }),
    supplier_patterns=tuple([
        SupplierPattern("Action", re.compile(r"\baction\b", re.IGNORECASE)),
        SupplierPattern("Leclerc", re.compile(r"\bleclerc\b|\be\.leclerc\b", re.IGNORECASE)),
        SupplierPattern("Tanger Marche", re.compile(r"\btanger\s+marche\b", re.IGNORECASE)),
        SupplierPattern("Sneha", re.compile(r"\bsneha\b", re.IGNORECASE)),
        SupplierPattern("Chandra Foods", re.compile(r"\bchandra\s+foods\b", re.IGNORECASE)),
        SupplierPattern("Lidl", re.compile(r"\blidl\b", re.IGNORECASE)),
        SupplierPattern("MV BRAZ - AU BRA", re.compile(r"\bmv\s*braz\s*-\s*au\s*bra\b", re.IGNORECASE)),
    ])
)
