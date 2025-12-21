
# tests/domain/reporting/test_category_breakdown_v2.py
import datetime as dt
import pytest

from bank_analysis.domain.entities import Transaction
from bank_analysis.domain.reporting.category_rules import DEFAULT_CATEGORY_RULES
from bank_analysis.domain.reporting.policies import DEFAULT_POLICY
from bank_analysis.domain.reporting.enhanced_breakdown import compute_category_breakdown
from bank_analysis.domain.value_objects import BreakdownKind


def mk_tx(
    amount: float,
    category: str | None = None,
    date: dt.date = dt.date(2025, 1, 15),
    month: str = "01-2025",
    message: str ="DEFAULT MESSSAGE",
    parent: str | None = None,
    supplier: str | None = None,

) -> Transaction:
    """
    Helper to build a Transaction for tests.
    Adjust field names here if your Transaction differs.
    """
    return Transaction(
        date_op=date,
        month=month,
        amount=amount,
        category=category,
        category_parent=parent,
        supplier=supplier,
        message=message
    )


def find(rows, *, kind: BreakdownKind, label: str):
    """
    Find a breakdown row by (kind, label).
    Returns (total, nb_operations) or (0.0, 0) if not found.
    """
    for r in rows:
        if r.kind == kind and r.label == label:
            return r.total, r.nb_operations
    return 0.0, 0


def breakdown_by_kind(rows, kind: BreakdownKind):
    """
    Filter rows by kind.
    """
    return [r for r in rows if r.kind == kind]


# ----------------------------
# SALARY
# ----------------------------

def test_salary_positive_only_is_counted():
    txs = [
        mk_tx(3000.0, "Salaire fixe"),
        mk_tx(2800.0, "Salaire fixe"),
        mk_tx(100.0, "Other credit"),   # non-salary credit -> ignored
        mk_tx(-50.0, "Groceries"),      # expense -> not counted in SALARY
    ]
    rows = compute_category_breakdown(txs, policy=DEFAULT_POLICY, rules=DEFAULT_CATEGORY_RULES)

    total, count = find(rows, kind=BreakdownKind.SALARY, label="Salaire fixe")
    assert total == 5800.0
    assert count == 2

    salary_rows = breakdown_by_kind(rows, BreakdownKind.SALARY)
    assert len(salary_rows) == 1
    assert salary_rows[0].label == "Salaire fixe"

# ----------------------------
# MANDATORY
# ----------------------------

def test_mandatory_exact_match_case_insensitive_canonical_label():
    # Both 'Impôts & taxes' variants should fold into the canonical label from rules.
    txs = [
        mk_tx(-1200.0, "Impôts & taxes"),
        mk_tx(-150.0, "impôts & taxes"),    # different casing -> still mandatory
    ]
    rows = compute_category_breakdown(txs, policy=DEFAULT_POLICY, rules=DEFAULT_CATEGORY_RULES)

    total, count = find(rows, kind=BreakdownKind.MANDATORY, label="Impôts & taxes")
    assert total == 1350.0
    assert count == 2

    # Ensure no duplicate labels due to casing differences
    mand_rows = breakdown_by_kind(rows, BreakdownKind.MANDATORY)
    labels = {r.label for r in mand_rows}
    assert labels == {"Impôts & taxes"}


def test_mandatory_is_exclusive_not_in_other():
    txs = [
        mk_tx(-80.0, "Téléphonie (fixe et mobile)"),
        mk_tx(-45.0, "Courses"),
    ]
    rows = compute_category_breakdown(txs, policy=DEFAULT_POLICY, rules=DEFAULT_CATEGORY_RULES)
    total_mand, _ = find(rows, kind=BreakdownKind.MANDATORY, label="Téléphonie (fixe et mobile)")
    assert total_mand == 80.0

    other_rows = breakdown_by_kind(rows, BreakdownKind.OTHER)
    assert all(r.label != "Téléphonie (fixe et mobile)" for r in other_rows)


# ----------------------------
# SUPPLIER (regex + exclusion from OTHER)
# ----------------------------

@pytest.mark.parametrize(
    "supplier_string, expected_label",
    [
        ("E.Leclerc Hyper", "Leclerc"),
        ("leclerc drive", "Leclerc"),
        ("ACTION Store", "Action"),
        ("MV BRAZ - AU BRA", "MV BRAZ - AU BRA"),
        ("Tanger   Marche", "Tanger Marche"),
        ("Chandra Foods - Paris", "Chandra Foods"),
        ("LIDL - FR", "Lidl"),
        ("Sneha Market", "Sneha"),
    ],
)
def test_supplier_regex_detection_and_exclusion_from_other(supplier_string, expected_label):
    txs = [
        mk_tx(-42.0, "Courses", supplier=supplier_string),
        mk_tx(-10.0, "Courses"),  # another expense without supplier -> goes to OTHER
    ]
    rows = compute_category_breakdown(txs, policy=DEFAULT_POLICY, rules=DEFAULT_CATEGORY_RULES)

    total_supp, count_supp = find(rows, kind=BreakdownKind.SUPPLIER, label=expected_label)
    assert total_supp == 42.0
    assert count_supp == 1

    # Supplier line must NOT also appear in OTHER (zero double-counting)
    other_rows = breakdown_by_kind(rows, BreakdownKind.OTHER)
    assert all(r.label != expected_label for r in other_rows)
    assert sum(r.total for r in other_rows) == 10.0  # only the non-supplier expense


# ----------------------------
# REIMBURSEMENTS (merged single row)
# ----------------------------

def test_reimbursements_are_merged_single_line():
    txs = [
        mk_tx(30.0, "Remboursement"),
        mk_tx(20.0, "remboursement de frais"),
        mk_tx(50.0, "Remboursements"),
        mk_tx(-5.0, "Courses"),
    ]
    rows = compute_category_breakdown(txs, policy=DEFAULT_POLICY, rules=DEFAULT_CATEGORY_RULES)

    total_reimb, count_reimb = find(rows, kind=BreakdownKind.REIMBURSEMENTS, label="Remboursements")
    assert total_reimb == -100.0  # 30 + 20 + 50
    assert count_reimb == 3

    reimb_rows = breakdown_by_kind(rows, BreakdownKind.REIMBURSEMENTS)
    assert len(reimb_rows) == 1


# ----------------------------
# OTHER (remaining aggregation)
# ----------------------------

def test_other_categories_aggregate_remaining_expenses_only():
    txs = [
        mk_tx(-12.0, "Courses"),
        mk_tx(-5.0, None),                     # missing category -> 'Autres'
        mk_tx(100.0, "Misc sale"),             # non-salary credit -> ? will still be counted
        mk_tx(-20.0, "Téléphonie (fixe et mobile)"),  # mandatory -> excluded from OTHER
        mk_tx(-7.0, "Remboursement de frais"),        # reimbursements -> excluded from OTHER
        mk_tx(-3.0, "Courses", supplier="LIDL FR"),   # supplier -> excluded from OTHER
    ]
    rows = compute_category_breakdown(txs, policy=DEFAULT_POLICY, rules=DEFAULT_CATEGORY_RULES)
    total_courses, count_courses = find(rows, kind=BreakdownKind.OTHER, label="Courses")
    assert total_courses == 12.0 and count_courses == 1  # supplier line not counted in OTHER

    total_autres, count_autres = find(rows, kind=BreakdownKind.OTHER, label="Autres")
    assert total_autres == 5.0 and count_autres == 1  # None -> 'Autres'

    other_rows = breakdown_by_kind(rows, BreakdownKind.OTHER)
    forbidden = {
        "Téléphonie (fixe et mobile)",
        "Remboursements",
        "Lidl",
    }
    assert all(r.label not in forbidden for r in other_rows)


# ----------------------------
# INTERNAL TRANSFERS (policy exclusion)
# ----------------------------

def test_internal_transfers_are_excluded_by_policy():
    excluded = next(iter(DEFAULT_POLICY.exclude_parents))
    txs = [
        mk_tx(-100.0, "Courses", parent=excluded),
        mk_tx(-50.0, "Courses", parent=None),
    ]
    rows = compute_category_breakdown(txs, policy=DEFAULT_POLICY, rules=DEFAULT_CATEGORY_RULES)

    # Only the non-excluded parent contributes
    total_courses, count_courses = find(rows, kind=BreakdownKind.OTHER, label="Courses")
    assert total_courses == 50.0
    assert count_courses == 1


# ----------------------------
# ZERO DOUBLE-COUNTING (composite scenario)
# ----------------------------

def test_zero_double_counting_across_kinds():
    txs = [
        mk_tx(3500.0, "Salaire fixe"),
        mk_tx(-40.0, "Impôts & taxes"),             # mandatory
        mk_tx(-25.0, "Remboursement de frais"),     # reimbursements
        mk_tx(-30.0, "Courses", supplier="E.Leclerc"),
        mk_tx(-10.0, "Courses"),                    # other
    ]
    rows = compute_category_breakdown(txs, policy=DEFAULT_POLICY, rules=DEFAULT_CATEGORY_RULES)
    # SALARY
    assert find(rows, kind=BreakdownKind.SALARY, label="Salaire fixe") == (3500.0, 1)

    # MANDATORY (canonicalized)
    assert find(rows, kind=BreakdownKind.MANDATORY, label="Impôts & taxes") == (40.0, 1)

    # REIMBURSEMENTS
    assert find(rows, kind=BreakdownKind.REIMBURSEMENTS, label="Remboursements") == (25.0, 1)

    # SUPPLIER (Leclerc)
    assert find(rows, kind=BreakdownKind.SUPPLIER, label="Leclerc") == (30.0, 1)

    # OTHER (Courses) -> only the non-supplier line
    assert find(rows, kind=BreakdownKind.OTHER, label="Courses") == (10.0, 1)

    # Cross-kind checks: ensure labels do not appear under multiple kinds
    kinds_per_label = {}
    for r in rows:
        kinds_per_label.setdefault(r.label, set()).add(r.kind)
    assert kinds_per_label["Courses"] == {BreakdownKind.OTHER}
    assert kinds_per_label["Leclerc"] == {BreakdownKind.SUPPLIER}
    assert kinds_per_label["Impôts & taxes"] == {BreakdownKind.MANDATORY}
    assert kinds_per_label["Salaire fixe"] == {BreakdownKind.SALARY}
    assert kinds_per_label["Remboursements"] == {BreakdownKind.REIMBURSEMENTS}
