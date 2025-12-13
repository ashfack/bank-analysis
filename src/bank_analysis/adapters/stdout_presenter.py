
from typing import Sequence, Any, List
from dataclasses import asdict, is_dataclass
from ..domain.reporting.policies import DEFAULT_POLICY
from ..ports.presenter import PresenterPort
from ..domain.value_objects import (
  MonthlySummary, CategoryBreakdown, AggregateMetrics, FilteredSummary
)

class StdoutPresenter(PresenterPort):
    def present_monthly_summary(self, rows: Sequence[MonthlySummary]) -> None:
        print("\n=== Monthly Summary ===")
        if not rows:
            print("(no data)")
            return
        self._print_table(
            rows,
            columns=[
                ("month", "Month"),
                ("total_salary", "Total Salary"),
                ("total_expenses", "Total Expenses"),
                ("nb_expense_operations", "# Expense Ops"),
                ("total_savings", "Total Savings"),
                ("total_savings_vs_theoretical", "Savings vs Theoretical"),
            ],
            formats={
                "total_salary": self._fmt_money,
                "total_expenses": self._fmt_money,
                "total_savings": self._fmt_money,
                "total_savings_vs_theoretical": self._fmt_money,
                "nb_expense_operations": lambda v: f"{int(v)}",
            },
        )

    def present_filtered_summary(self, result: FilteredSummary) -> None:
        excluded_months = result.excluded_months or []
        print("\nExcluded months:", ", ".join(excluded_months) if excluded_months else "None")
        print("\n=== Filtered Summary (normal months) ===")
        rows = result.filtered
        if not rows:
            print("(no data)")
            return
        self._print_table(
            rows,
            columns=[
                ("month", "Month"),
                ("total_salary", "Total Salary"),
                ("total_expenses", "Total Expenses"),
                ("nb_expense_operations", "# Expense Ops"),
                ("total_savings", "Total Savings"),
                ("total_savings_vs_theoretical", "Savings vs Theoretical"),
            ],
            formats={
                "total_salary": self._fmt_money,
                "total_expenses": self._fmt_money,
                "total_savings": self._fmt_money,
                "total_savings_vs_theoretical": self._fmt_money,
                "nb_expense_operations": lambda v: f"{int(v)}",
            },
        )

    def present_aggregates(self, aggregates: AggregateMetrics) -> None:
        print("\n=== Aggregate Metrics ===")
        print(f"Average savings: {aggregates.mean_savings:.2f} €")
        print(
            f"Average savings vs theoretical salary "
            f"({DEFAULT_POLICY.REF_THEORETICAL_SALARY:.0f} €): "
            f"{aggregates.mean_savings_vs_theoretical:.2f} €"
        )

    def present_category_breakdown(self, rows: Sequence[CategoryBreakdown]) -> None:
        print("\n=== Category Breakdown (Advanced Mode) ===")
        if not rows:
            print("(no data)")
            return
        self._print_table(
            rows,
            columns=[
                ("month", "Month"),
                ("category_parent", "Category Parent"),
                ("total", "Total"),
                ("nb_operations", "# Ops"),
            ],
            formats={
                "total": self._fmt_money,
                "nb_operations": lambda v: f"{int(v)}",
            },
        )

    # === Internal helpers ===

    @staticmethod
    def _fmt_money(v: Any) -> str:
        try:
            return f"{float(v):.2f}"
        except Exception:
            return str(v)

    def _print_table(
        self,
        rows: Sequence[Any],
        columns: List[tuple],
        formats: dict | None = None,
    ) -> None:
        """
        Print a list of DTOs/dicts as a formatted table with headers.

        Args:
            rows: Sequence of dataclass instances or dicts.
            columns: List of (field_name, header_label) in desired order.
            formats: Optional dict mapping field_name -> formatter(value)->str.
        """
        formats = formats or {}

        # Convert rows to list of dicts
        dict_rows: List[dict] = []
        for r in rows:
            if is_dataclass(r):
                dict_rows.append(asdict(r))
            elif isinstance(r, dict):
                dict_rows.append(r)
            else:
                # Fallback: try __dict__
                dict_rows.append(getattr(r, "__dict__", {"value": r}))

        # Build string matrix applying formats
        headers = [hdr for _, hdr in columns]
        matrix: List[List[str]] = []
        for d in dict_rows:
            line: List[str] = []
            for field, _hdr in columns:
                val = d.get(field, "")
                fmt = formats.get(field)
                s = fmt(val) if fmt else str(val)
                line.append(s)
            matrix.append(line)

        # Compute column widths
        widths = [len(h) for h in headers]
        for row in matrix:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], len(cell))

        # Render header
        header_line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
        print(header_line)
        print("  ".join("-" * w for w in widths))

        # Render rows
        for row in matrix:
            print("  ".join(row[i].ljust(widths[i]) for i in range(len(row))))
