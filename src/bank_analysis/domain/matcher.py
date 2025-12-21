from typing import Optional, Tuple

from bank_analysis.domain.reporting.category_rules import SupplierPattern


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