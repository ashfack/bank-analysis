import argparse
from ..adapters.csv_loader import CsvDataLoader
from ..usecases.analyze_budget import AnalyzeBudgetUseCase
from ..ports.presenter import PresenterPort
from ..domain import analysis as domain_analysis

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

def choose_file_interactive(files):
    print("Available CSV files:")
    for i, f in enumerate(files, start=1):
        print(f"{i} - {f}")
    while True:
        try:
            choice = int(input("Enter the number of the file to use: "))
            if 1 <= choice <= len(files):
                return files[choice - 1]
            else:
                print("Invalid number, please try again.")
        except ValueError:
            print("Please enter a valid number.")

def run(argv=None):
    parser = argparse.ArgumentParser(prog="bank-analysis")
    parser.add_argument("--csv", "-c", help="Path to accounts CSV")
    args = parser.parse_args(argv)

    loader = CsvDataLoader(base_path=".")
    presenter = StdoutPresenter()
    uc = AnalyzeBudgetUseCase(loader, presenter)

    if args.csv:
        csv_path = args.csv
    else:
        files = loader.list_csv_files()
        if not files:
            print("No CSV files found in the current directory.")
            return
        csv_path = choose_file_interactive(files)

    print(f"\nSelected file: {csv_path}\n")

    choice = input("\nDo you want to exclude atypical months (negative savings or deviation)? (y/n): ").strip().lower()
    do_filter = choice == "y"

    choice = input("\nDo you want to see the category breakdown ? (y/n): ").strip().lower()
    show_breakdown = choice == "y"

    export_choice = input("\nDo you want to export the filtered summary and category breakdown to CSV? (y/n): ").strip().lower()
    export_paths = None
    if export_choice == "y":
        export_paths = {"summary": "filtered_summary.csv", "breakdown": "category_breakdown.csv"}

    uc.run_from_path(csv_path, do_filter_atypical=do_filter, show_category_breakdown=show_breakdown, export_paths=export_paths)

if __name__ == "__main__":
    run()