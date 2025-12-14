from flask import Flask, request, render_template, redirect, url_for, flash, jsonify, session
import os

from bank_analysis.domain.value_objects import BreakdownKind
from bank_analysis.usecases.compute_enhanced_category_breakdown import \
  ComputeEnhancedCategoryBreakdownUseCase
from bank_analysis.adapters.calendar_cycle import CalendarCycleGrouper
from bank_analysis.adapters.salary_cycle import SalaryCycleGrouper
from bank_analysis.infrastructure import period_splicer
from bank_analysis.adapters.csv_content_loader import CsvContentDataLoader
from bank_analysis.usecases.compute_category_breakdown import \
  ComputeCategoryBreakdownUseCase
from bank_analysis.usecases.compute_monthly_summary import \
  ComputeMonthlySummaryUseCase
from bank_analysis.usecases.data_loading import DataLoadingUseCase
from bank_analysis.adapters.result_in_memory_store import InMemoryResultStore
from bank_analysis.usecases.filter_atypical_months import \
  FilterAtypicalMonthsUseCase

app = Flask(__name__)
app.secret_key = "change-me-in-production"
result_store = InMemoryResultStore()


ALLOWED_EXTENSIONS = {"csv", "txt"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    # Accept file upload OR pasted CSV text
    csv_text = None
    if "file" in request.files and request.files["file"].filename != "":
        f = request.files["file"]
        if not allowed_file(f.filename):
            flash("Only CSV or TXT files are allowed.")
            return redirect(url_for("index"))
        csv_text = f.read().decode("utf-8")
    else:
        csv_text = request.form.get("csv_text", "").strip()

    if not csv_text:
        flash("Please upload a CSV file or paste CSV data.")
        return redirect(url_for("index"))

    try:


        # Read the cycle from form; default to calendar
        cycle = request.form.get("cycle", "calendar")
        cycle_grouper = None

        loader = CsvContentDataLoader(base_path=".")
        data_loader_uc = DataLoadingUseCase(loader)

        transactions = data_loader_uc.execute(csv_text)

        if cycle == "calendar": cycle_grouper = CalendarCycleGrouper()
        elif cycle == "salary": cycle_grouper = SalaryCycleGrouper(transactions)


        monthly_summary_uc = ComputeMonthlySummaryUseCase(cycle_grouper)
        filtering_outliers_uc = FilterAtypicalMonthsUseCase()



        custom_analysis = monthly_summary_uc.execute(transactions)
        filtering_outlier = request.form.get("filtering_outlier", "yes")
        if filtering_outlier == "yes":
            custom_analysis = filtering_outliers_uc.execute(custom_analysis).filtered
    except Exception as e:
        flash(f"Could not parse CSV: {e}")
        return redirect(url_for("index"))

    # Call your refactored analysis function
    transactions = loader.load_and_prepare(csv_text)

    # Store DF in session-aware cache
    session_id = session.get("_id") or os.urandom(16).hex()
    session["_id"] = session_id
    result_store.put(session_id, transactions)


    # results should be JSON-serializable dict with keys used in the template
    return render_template("results.html", results={}, customAnalysis=custom_analysis)


KIND_ORDER = {
    BreakdownKind.SALARY: 0,
    BreakdownKind.MANDATORY: 1,
    BreakdownKind.SUPPLIER: 2,
    BreakdownKind.OTHER: 3,
    BreakdownKind.REIMBURSEMENTS: 4,
}

def breakdown_sort_key(row):
    """
    Sort rows by:
      1) kind order (SALARY, MANDATORY, SUPPLIER, OTHER, REIMBURSEMENTS)
      2) then label (label) ascending
      3) then total descending (optional)
    """
    kind_rank = KIND_ORDER.get(row.kind, 99)
    # total descending -> use negative value
    return (kind_rank, row.label.lower(), -row.total)


@app.route("/details")
def details():
    period = request.args.get("period")
    session_id = session.get("_id")
    if not period or not session_id:
        return jsonify([])

    transactions = result_store.get(session_id)
    if transactions is None:
        return jsonify([])

    spliced_transactions = period_splicer.filter_transactions_by_period(transactions, period)

    breakdown_style = request.args.get("breakdown_style", "default")
    if breakdown_style == "enhanced":
      breakdown_uc = ComputeEnhancedCategoryBreakdownUseCase()
    else:
      breakdown_uc = ComputeCategoryBreakdownUseCase()

    breakdown = breakdown_uc.execute(spliced_transactions)

    ordered = sorted(breakdown, key=breakdown_sort_key)

    data = jsonify([{"category_parent": row.label, "total": row.total,
                  "nb_operations": row.nb_operations, "kind": row.kind.value}
                 for row in ordered])
    return data


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
