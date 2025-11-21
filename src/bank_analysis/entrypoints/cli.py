import argparse
from ..adapters.csv_loader import CsvDataLoader
from ..usecases.analyze_budget import AnalyzeBudgetUseCase
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