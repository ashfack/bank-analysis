from collections import defaultdict
from typing import Sequence, List, Dict, Optional, Tuple

from bank_analysis.domain.entities import Transaction
from bank_analysis.domain.reporting.policies import BudgetPolicy, DEFAULT_POLICY
from bank_analysis.domain.reporting.category_rules import (
    CategoryRules,
    DEFAULT_CATEGORY_RULES,
    SupplierPattern,
)
from bank_analysis.domain.value_objects import CategoryBreakdown, BreakdownKind


def _case_insensitive_equal(a: Optional[str], b: Optional[str]) -> bool:
    """
    Case-insensitive, trimmed equality for strings.
    Returns False if either is None.
    """
    if a is None or b is None:
        return False
    return a.strip().casefold() == b.strip().casefold()


def _contains_any(text: Optional[str], needles_lower: Tuple[str, ...]) -> bool:
    """
    Case-insensitive substring detection; returns True if any needle is found in text.
    """
    if not text:
        return False
    t = text.casefold()
    return any(n in t for n in needles_lower)


def _match_supplier(supplier_found: Optional[str], patterns: Tuple[SupplierPattern, ...]) -> Optional[str]:
    """
    Try to match 'supplier_found' against known supplier regex patterns.
    Returns the supplier display name if matched; otherwise None.
    """
    if not supplier_found:
        return None
    s = supplier_found.strip().casefold()
    for sp in patterns:
        if sp.regex.search(s):
            return sp.name
    return None


def compute_category_breakdown(
    transactions: Sequence[Transaction],
    policy: BudgetPolicy = DEFAULT_POLICY,
    rules: CategoryRules = DEFAULT_CATEGORY_RULES,
) -> List[CategoryBreakdown]:
    """
    Compute a flat list of CategoryBreakdown rows over the provided transactions (no period grouping).
    Enforces zero double-counting under the following semantics:

      - SALARY:
          'Salaire fixe' with positive amounts only (exact, case-insensitive)
      - MANDATORY:
          exact match (case-insensitive) against rules.mandatory_categories
          label canonicalized to the rule's original spelling
      - REIMBURSEMENTS:
          merged into a single row labeled 'Remboursements' for all reimbursements
      - SUPPLIER:
          supplier-specific rows (regex match on supplier_found), excluded from OTHER
      - OTHER:
          remaining expenses (negative amounts) not classified as INTERNAL, SALARY, MANDATORY,
          REIMBURSEMENTS, or SUPPLIER. Category None maps to 'Autres'.

    Notes:
      - INTERNAL transfers (category_parent ∈ policy.exclude_parents) are excluded entirely.
      - Non-salary credits (amount >= 0) are ignored for expense sections.
      - Expense totals use absolute values of negative amounts.
    """
    # Prepare canonicalization map for mandatory categories (lower -> canonical)
    mandatory_map = {m.casefold(): m for m in rules.mandatory_categories}
    reimbursement_needles = tuple(k.casefold() for k in rules.reimbursement_keywords)
    salary_label = rules.salary_category
    REIMBURSE_LABEL = "Remboursements"

    # Accumulators: kind -> label -> total / count
    acc_total: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    acc_count: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for tx in transactions:
        # Classification flags
        is_internal = (tx.category_parent in policy.exclude_parents) if tx.category_parent else False
        is_salary = _case_insensitive_equal(tx.category, salary_label) and (tx.amount > 0)

        cat_lower = (tx.category or "").casefold()
        is_mandatory = cat_lower in mandatory_map
        is_reimbursement = _contains_any(tx.category, reimbursement_needles)
        supplier_name = _match_supplier(getattr(tx, "supplier", None), rules.supplier_patterns)

        # SALARY (positive amounts only)
        if is_salary:
            acc_total["SALARY"][salary_label] += float(tx.amount)
            acc_count["SALARY"][salary_label] += 1
            continue  # excluded from expense sections

        amount_abs = -float(tx.amount)

        # Exclude internal transfers
        if is_internal:
            continue

        # MANDATORY (canonical label)
        if is_mandatory:
            label = mandatory_map[cat_lower]
            acc_total["MANDATORY"][label] += amount_abs
            acc_count["MANDATORY"][label] += 1
            continue  # excluded from other sections

        # REIMBURSEMENTS (merged)
        if is_reimbursement:
            acc_total["REIMBURSEMENTS"][REIMBURSE_LABEL] += amount_abs
            acc_count["REIMBURSEMENTS"][REIMBURSE_LABEL] += 1
            continue  # excluded from other sections

        # SUPPLIER (excluded from OTHER)
        if supplier_name is not None:
            acc_total["SUPPLIER"][supplier_name] += amount_abs
            acc_count["SUPPLIER"][supplier_name] += 1
            continue

        # OTHER (remaining expenses)
        label = (tx.category or "Autres").strip()
        acc_total["OTHER"][label] += amount_abs
        acc_count["OTHER"][label] += 1

    # Build flat, ordered rows
    rows: List[CategoryBreakdown] = []
    for kind in (
        BreakdownKind.SALARY,
        BreakdownKind.MANDATORY,
        BreakdownKind.SUPPLIER,
        BreakdownKind.OTHER,
        BreakdownKind.REIMBURSEMENTS
    ):
        labels = acc_total.get(kind.value, {})
        for label in sorted(labels.keys()):
            total = round(labels[label], 2)
            count = acc_count[kind.value].get(label, 0)
            rows.append(
                CategoryBreakdown(
                    label=label,  # generic display label
                    total=total,
                    nb_operations=count,
                    kind=kind,
                )
            )
    return rows
