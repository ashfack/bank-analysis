import argparse

from bank_analysis.adapters.salary_cycle import SalaryCycleGrouper
from src.bank_analysis.usecases.compute_aggregates import \
  ComputeAggregatesUseCase
from src.bank_analysis.usecases.compute_category_breakdown import \
  ComputeCategoryBreakdownUseCase
from src.bank_analysis.usecases.compute_monthly_summary import \
  ComputeMonthlySummaryUseCase
from src.bank_analysis.usecases.data_loading import DataLoadingUseCase
from src.bank_analysis.usecases.export_use_case import ExportUseCase
from src.bank_analysis.usecases.filter_atypical_months import \
  FilterAtypicalMonthsUseCase
from ..adapters.csv_file_loader import CsvFileDataLoader
from ..adapters.stdout_presenter import StdoutPresenter

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

    loader = CsvFileDataLoader(base_path=".")

    data_loader_uc = DataLoadingUseCase(loader)

    filter_uc = FilterAtypicalMonthsUseCase()
    aggregates_uc = ComputeAggregatesUseCase()
    category_breakdown_uc = ComputeCategoryBreakdownUseCase()
    export_uc = ExportUseCase()

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

    presenter = StdoutPresenter()

    transactions = data_loader_uc.execute(csv_path)

    cycle_grouper = SalaryCycleGrouper(transactions)
    monthly_summary_uc = ComputeMonthlySummaryUseCase(cycle_grouper)

    monthly_summary = monthly_summary_uc.execute(transactions)
    summary=monthly_summary
    presenter.present_monthly_summary(monthly_summary)

    if do_filter:
        filtered_atypical_months = filter_uc.execute(monthly_summary)
        summary=filtered_atypical_months.filtered
        presenter.present_filtered_summary(filtered_atypical_months)
        aggregates = aggregates_uc.execute(summary)
    else:
        aggregates = aggregates_uc.execute(monthly_summary)

    presenter.present_aggregates(aggregates)

    category_breakdown = None
    if show_breakdown:
        category_breakdown = category_breakdown_uc.execute(transactions)
        presenter.present_category_breakdown(category_breakdown)
    
    if export_choice == "y":
        export_paths = {"summary": "summary.csv", "breakdown": "category_breakdown.csv"}
        export_uc.execute(export_paths, summary, category_breakdown)


if __name__ == "__main__":
    run()