
from ..ports.presenter import PresenterPort

class StdoutPresenter(PresenterPort):
    def present_monthly_summary(self, df):
        print("\n=== Monthly Summary ===")
        print(df.to_string(index=False))

    def present_filtered_summary(self, df, excluded_months):
        print("\nExcluded months:", ", ".join(excluded_months) if excluded_months else "None")
        print("\n=== Filtered Summary (normal months) ===")
        print(df.to_string(index=False))

    def present_aggregates(self, aggregates: domain_analysis.AggregateMetrics):
        print("\n=== Aggregate Metrics ===")
        print(f"Average savings: {aggregates.mean_savings:.2f} €")
        print(f"Average savings vs theoretical salary ({domain_analysis.REF_THEORETICAL_SALARY:.0f} €): {aggregates.mean_savings_vs_theoretical:.2f} €")

    def present_category_breakdown(self, df):
        print("\n=== Category Breakdown (Advanced Mode) ===")
        print(df.to_string(index=False))