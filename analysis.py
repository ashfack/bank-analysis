"""
Refactor your CLI analysis logic here. The CLI should call functions from this module.
This example assumes a CSV with columns such as: date, amount, category, description.
Return a dict with serializable summary info for templates or APIs.
"""
import pandas as pd

def analyze_dataframe(df: pd.DataFrame) -> dict:
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]

    # Parse date column if present
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Ensure amount exists and is numeric
    if "amount" in df.columns:
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    else:
        raise ValueError("CSV must contain an 'amount' column")

    if "category" not in df.columns:
        df["category"] = "uncategorized"

    total = float(df["amount"].sum())

    monthly = []
    if "date" in df.columns:
        monthly_totals = df.dropna(subset=["date"]).set_index("date").resample("M")["amount"].sum()
        monthly = [{"month": idx.strftime("%Y-%m"), "total": float(v)} for idx, v in monthly_totals.items()]

    category_totals = df.groupby("category")["amount"].sum().sort_values(ascending=False)
    categories = [{"category": c, "total": float(v)} for c, v in category_totals.items()]

    sample_rows = df.head(50).to_dict(orient="records")

    return {
        "total": total,
        "monthly": monthly,
        "categories": categories,
        "sample_rows": sample_rows,
        "n_rows": len(df),
    }