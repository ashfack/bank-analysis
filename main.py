import os
import pandas as pd
import unicodedata

# ========================= CONFIGURATION =========================
SALARY_CATEGORY = "Salaire fixe"  # Column name remains in French as per input file
EXCLUDE_EXPENSE_PARENTS = {"Mouvements internes débiteurs", "Mouvements internes créditeurs"}
REF_THEORETICAL_SALARY = 3700.0

# ========================= UTILITIES =========================
def _strip_nbsp(s: str) -> str:
    """Remove non-breaking spaces and normalize string."""
    if not isinstance(s, str):
        return s
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("\xa0", " ").replace("\u202f", " ")
    return s.strip().replace(" ", "")

def parse_amount(value):
    """Convert value to float, handle special cases."""
    if pd.isna(value):
        return pd.NA
    s = _strip_nbsp(str(value))
    if s == "":
        return pd.NA
    s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        s = s.replace('"', '')
        try:
            return float(s)
        except ValueError:
            return pd.NA

# ========================= FILE SELECTION =========================
def list_csv_files():
    """List all CSV files in the current directory."""
    files = [f for f in os.listdir('.') if f.lower().endswith('.csv')]
    if not files:
        print("No CSV files found in the current directory.")
        return []
    print("Available CSV files:")
    for i, f in enumerate(files, start=1):
        print(f"{i} - {f}")
    return files

def choose_file(files):
    """Prompt user to choose a file by number."""
    while True:
        try:
            choice = int(input("Enter the number of the file to use: "))
            if 1 <= choice <= len(files):
                return files[choice - 1]
            else:
                print("Invalid number, please try again.")
        except ValueError:
            print("Please enter a valid number.")

# ========================= DATA LOADING =========================
def load_and_prepare(csv_path):
    """Load CSV and prepare necessary columns."""
    df = pd.read_csv(csv_path, sep=";", dtype=str, encoding="utf-8")
    df["dateOp"] = pd.to_datetime(df["dateOp"], errors="coerce", format="%Y-%m-%d")
    df["amount"] = df["amount"].apply(parse_amount).astype("Float64")
    df["month"] = df["dateOp"].dt.to_period("M").astype(str)
    return df

# ========================= CALCULATIONS =========================
def compute_monthly_summary(df):
    """Compute monthly summary: salaries, expenses, savings."""
    salaries = df.loc[df["category"] == SALARY_CATEGORY].groupby("month")["amount"].sum().rename("total_salary")
    mask_non_internal = ~df["categoryParent"].isin(EXCLUDE_EXPENSE_PARENTS)
    mask_neg = df["amount"] < 0
    expenses_df = df.loc[mask_non_internal & mask_neg]
    expenses = expenses_df.groupby("month")["amount"].sum().abs().rename("total_expenses")
    nb_ops = expenses_df.groupby("month")["amount"].count().rename("nb_expense_operations")
    out = pd.concat([salaries, expenses, nb_ops], axis=1).fillna(0.0)
    out["total_savings"] = out["total_salary"] - out["total_expenses"]
    out["total_savings_vs_theoretical"] = REF_THEORETICAL_SALARY - out["total_expenses"]
    return out.round(2).reset_index().sort_values("month")

def compute_category_breakdown(df):
    """Advanced mode: breakdown by category parent (total + number of operations)."""
    mask_non_internal = ~df["categoryParent"].isin(EXCLUDE_EXPENSE_PARENTS)
    mask_neg = df["amount"] < 0
    expenses_df = df.loc[mask_non_internal & mask_neg]
    grouped = expenses_df.groupby(["month", "categoryParent"])
    summary = grouped["amount"].agg(["sum", "count"]).reset_index()
    summary.rename(columns={"sum": "total", "count": "nb_operations"}, inplace=True)
    summary["total"] = summary["total"].abs().round(2)
    return summary.sort_values(["month", "categoryParent"])

def filter_atypical_months(summary_df):
    """Exclude months with negative savings or deviation."""
    excluded_months = summary_df.loc[
        (summary_df["total_savings"] < 0) | (summary_df["total_savings_vs_theoretical"] < 0),
        "month"
    ].tolist()
    filtered_df = summary_df[~summary_df["month"].isin(excluded_months)]
    return filtered_df, excluded_months

def compute_aggregates(summary_df):
    """Compute aggregate averages."""
    return {
        "mean_savings": summary_df["total_savings"].mean(),
        "mean_savings_vs_theoretical": summary_df["total_savings_vs_theoretical"].mean()
    }

def export_to_csv(df, filename):
    """Export DataFrame to CSV."""
    df.to_csv(filename, index=False, sep=";")

# ========================= MAIN =========================
def main():
    files = list_csv_files()
    if not files:
        return
    chosen_file = choose_file(files)
    print(f"\nSelected file: {chosen_file}\n")

    df = load_and_prepare(chosen_file)

    # Monthly summary
    monthly_summary = compute_monthly_summary(df)
    print("\n=== Monthly Summary ===")
    print(monthly_summary.to_string(index=False))

    # Ask if user wants to exclude atypical months
    choice = input("\nDo you want to exclude atypical months (negative savings or deviation)? (y/n): ").strip().lower()
    if choice == "y":
        filtered_summary, excluded_months = filter_atypical_months(monthly_summary)
        print("\nExcluded months:", ", ".join(excluded_months) if excluded_months else "None")
        print("\n=== Filtered Summary (normal months) ===")
        print(filtered_summary.to_string(index=False))
        calc_df = filtered_summary
    else:
        calc_df = monthly_summary

    # Compute aggregates
    aggregates = compute_aggregates(calc_df)
    print("\n=== Aggregate Metrics ===")
    print(f"Average savings: {aggregates['mean_savings']:.2f} €")
    print(f"Average savings vs theoretical salary (3700 €): {aggregates['mean_savings_vs_theoretical']:.2f} €")

    # Advanced mode: category breakdown
    category_breakdown = compute_category_breakdown(df)
    print("\n=== Category Breakdown (Advanced Mode) ===")
    print(category_breakdown.to_string(index=False))

    # Export option
    export_choice = input("\nDo you want to export the filtered summary and category breakdown to CSV? (y/n): ").strip().lower()
    if export_choice == "y":
        export_to_csv(calc_df, "filtered_summary.csv")
        export_to_csv(category_breakdown, "category_breakdown.csv")
        print("\n✅ Export completed: filtered_summary.csv and category_breakdown.csv")

if __name__ == "__main__":
    main()