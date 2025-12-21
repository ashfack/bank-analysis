import types
import pytest

from bank_analysis.domain.reporting import filtering




# ---------- Helpers (lightweight stubs/fakes) ----------

class StubMonthlySummary:
    """Minimal stub to satisfy attributes used by filter_atypical_months."""
    def __init__(self, month, total_savings=0, total_savings_vs_theoretical=0):
        self.month = month
        self.total_savings = total_savings
        self.total_savings_vs_theoretical = total_savings_vs_theoretical

class StubFilteredSummary:
    """We validate structural behavior,
    we only need 'filtered' and 'excluded_months' attributes for assertions."""
    def __init__(self, filtered, excluded_months):
        self.filtered = filtered
        self.excluded_months = excluded_months

class StubTransaction:
    """Minimal stub to satisfy attributes used by filter_transactions_by_period_label_and_kind."""
    def __init__(self, category, supplier=None, meta=None):
        self.category = category
        # supplier may be absent or None; getattr handles it in the code under test
        if supplier is not ...:
            self.supplier = supplier
        # allow attaching any extra fields for test readability
        self.meta = meta or {}

# ---------- Fixtures ----------

@pytest.fixture(autouse=True)
def patch_filtered_summary_class(monkeypatch):
    """
    The code under test returns FilteredSummary(filtered=..., excluded_months=...).
    We monkeypatch to a simple stub that behaves similarly to the data class for assertions.
    """
    monkeypatch.setattr(filtering, "FilteredSummary", StubFilteredSummary, raising=True)


@pytest.fixture
def sample_transactions():
    return [
        StubTransaction(category="Food", supplier="CARREFOUR", meta={"id": 1}),
        StubTransaction(category="food", supplier="CARREFOUR CITY", meta={"id": 2}),
        StubTransaction(category="Rent", supplier="LANDLORD SARL", meta={"id": 3}),
        StubTransaction(category="Transport", supplier=None, meta={"id": 4}),
        StubTransaction(category="Food", supplier="FRANPRIX", meta={"id": 5}),
    ]


# ---------- Tests: filter_atypical_months ----------

def test_filter_atypical_months_empty():
    res = filtering.filter_atypical_months([])
    assert isinstance(res, StubFilteredSummary)
    assert res.filtered == []
    assert res.excluded_months == []


def test_filter_atypical_months_all_excluded_negative_savings():
    summary = [
        StubMonthlySummary("2024-01", total_savings=-1, total_savings_vs_theoretical=0),
        StubMonthlySummary("2024-02", total_savings=-100, total_savings_vs_theoretical=10),
    ]
    res = filtering.filter_atypical_months(summary)
    assert res.excluded_months == ["2024-01", "2024-02"]
    assert res.filtered == []


def test_filter_atypical_months_all_excluded_negative_theoretical():
    summary = [
        StubMonthlySummary("2024-03", total_savings=0, total_savings_vs_theoretical=-0.01),
        StubMonthlySummary("2024-04", total_savings=500, total_savings_vs_theoretical=-10),
    ]
    res = filtering.filter_atypical_months(summary)
    assert res.excluded_months == ["2024-03", "2024-04"]
    assert res.filtered == []


def test_filter_atypical_months_mixed_inclusion_order_preserved():
    # 2024-01 excluded (negative savings), 2024-03 excluded (negative theoretical)
    # 2024-02 and 2024-04 kept
    summary = [
        StubMonthlySummary("2024-01", total_savings=-1, total_savings_vs_theoretical=100),
        StubMonthlySummary("2024-02", total_savings=100, total_savings_vs_theoretical=50),
        StubMonthlySummary("2024-03", total_savings=10, total_savings_vs_theoretical=-1),
        StubMonthlySummary("2024-04", total_savings=0, total_savings_vs_theoretical=0),
    ]
    res = filtering.filter_atypical_months(summary)
    assert res.excluded_months == ["2024-01", "2024-03"]
    assert [s.month for s in res.filtered] == ["2024-02", "2024-04"]


# ---------- Tests: filter_transactions_by_period_label_and_kind ----------

def test_filter_transactions_by_period_calls_period_splicer_first(monkeypatch, sample_transactions):
    # Arrange: monkeypatch period_splicer to only pass through txs with meta.id in a given period
    captured = {}

    def fake_period_splicer(all_txs, period):
        captured["called_with"] = (all_txs, period)
        # Simulate: period '2024-01' contains id 1 and 3 only
        if period == "2024-01":
            return [t for t in all_txs if t.meta.get("id") in {1, 3}]
        return []

    monkeypatch.setattr(filtering.period_splicer, "filter_transactions_by_period", fake_period_splicer, raising=True)

    # Non-supplier kind → category matching (case-insensitive)
    res = filtering.filter_transactions_by_period_label_and_kind(
        transactions=sample_transactions,
        period="2024-01",
        label="food",
        kind=filtering.BreakdownKind.CATEGORY if hasattr(filtering.BreakdownKind, "CATEGORY") else filtering.BreakdownKind  # fallback if enum lacks CATEGORY
    )

    # Assert period filtering applied first, then category casefold.
    # From ids {1,3}, only id 1 has category Food
    assert [t.meta["id"] for t in res] == [1]
    assert captured["called_with"][1] == "2024-01"


def test_filter_transactions_by_period_label_case_insensitive(monkeypatch, sample_transactions):
    def fake_period_splicer(all_txs, period):
        # Return all to focus on label matching
        return list(all_txs)

    monkeypatch.setattr(filtering.period_splicer, "filter_transactions_by_period", fake_period_splicer, raising=True)

    # label 'FOOD' should match 'Food' and 'food'
    res = filtering.filter_transactions_by_period_label_and_kind(
        transactions=sample_transactions,
        period="ANY",
        label="FOOD",
        kind=getattr(filtering.BreakdownKind, "CATEGORY", filtering.BreakdownKind)
    )
    assert sorted(t.meta["id"] for t in res) == [1, 2, 5]


def test_filter_transactions_by_supplier_kind_uses_matcher_and_rules(monkeypatch, sample_transactions):
    # Keep only transactions with defined supplier; ensure one with None is present to test getattr(None)
    def fake_period_splicer(all_txs, period):
        return list(all_txs)

    # Capture calls to _match_supplier
    calls = []

    def fake_match_supplier(supplier_value, supplier_patterns):
        calls.append((supplier_value, tuple(supplier_patterns)))
        # Simple logic: pretend patterns accept suppliers containing 'CARREFOUR' or 'FRANPRIX'
        if supplier_value is None:
            return False
        s = supplier_value.upper()
        return ("CARREFOUR" in s) or ("FRANPRIX" in s)

    # Fake DEFAULT_CATEGORY_RULES with a simple structure exposing supplier_patterns
    fake_rules = types.SimpleNamespace(supplier_patterns=["carrefour.*", "franprix.*"])

    monkeypatch.setattr(filtering.period_splicer, "filter_transactions_by_period", fake_period_splicer, raising=True)
    monkeypatch.setattr(filtering, "_match_supplier", fake_match_supplier, raising=True)
    # Patch the object imported inside the module under test
    monkeypatch.setattr(filtering, "DEFAULT_CATEGORY_RULES", fake_rules, raising=True)

    res = filtering.filter_transactions_by_period_label_and_kind(
        transactions=sample_transactions,
        period="2024-02",
        label="(label ignored in SUPPLIER mode)",
        kind=filtering.BreakdownKind.SUPPLIER
    )

    # Expect only suppliers matching fake_match_supplier
    assert sorted(t.meta["id"] for t in res) == [1, 2, 5]

    # Ensure _match_supplier was called for each tx in period (5 calls total)
    assert len(calls) == len(sample_transactions)
    # Ensure supplier_patterns passed through consistently
    assert all(calls[0][1] == c[1] for c in calls)


def test_filter_transactions_by_supplier_kind_handles_missing_supplier_attr(monkeypatch):
    class TxNoSupplier:
        def __init__(self, category):
            self.category = category

    transactions = [TxNoSupplier("Misc")]

    def fake_period_splicer(all_txs, period):
        return list(all_txs)

    def fake_match_supplier(supplier_value, supplier_patterns):
        # Should receive None due to getattr(t, "supplier", None)
        return supplier_value is not None  # thus returns False for None

    fake_rules = types.SimpleNamespace(supplier_patterns=[".*"])

    monkeypatch.setattr(filtering.period_splicer, "filter_transactions_by_period", fake_period_splicer, raising=True)
    monkeypatch.setattr(filtering, "_match_supplier", fake_match_supplier, raising=True)
    monkeypatch.setattr(filtering, "DEFAULT_CATEGORY_RULES", fake_rules, raising=True)

    res = filtering.filter_transactions_by_period_label_and_kind(
        transactions=transactions,
        period="any",
        label="ignored",
        kind=filtering.BreakdownKind.SUPPLIER
    )

    assert res == []


def test_filter_transactions_non_supplier_kind_ignores_supplier_and_uses_label(monkeypatch, sample_transactions):
    def fake_period_splicer(all_txs, period):
        return list(all_txs)

    monkeypatch.setattr(filtering.period_splicer, "filter_transactions_by_period", fake_period_splicer, raising=True)

    # Choose label that only matches Transport (id 4). Supplier is None; should not matter in non-supplier mode.
    res = filtering.filter_transactions_by_period_label_and_kind(
        transactions=sample_transactions,
        period="any",
        label="transport",
        kind=getattr(filtering.BreakdownKind, "CATEGORY", filtering.BreakdownKind)
    )
    assert [t.meta["id"] for t in res] == [4]
