from flask import Flask, request, render_template, redirect, url_for, flash, jsonify, session
import os

from src.bank_analysis.adapters.calendar_cycle import CalendarCycleGrouper
from src.bank_analysis.adapters.salary_cycle import SalaryCycleGrouper
from src.bank_analysis.infrastructure import period_splicer
from src.bank_analysis.adapters.csv_content_loader import CsvContentDataLoader
from src.bank_analysis.usecases.compute_category_breakdown import \
  ComputeCategoryBreakdownUseCase
from src.bank_analysis.usecases.compute_monthly_summary import \
  ComputeMonthlySummaryUseCase
from src.bank_analysis.usecases.data_loading import DataLoadingUseCase
from src.bank_analysis.adapters.result_in_memory_store import InMemoryResultStore
from src.bank_analysis.usecases.filter_atypical_months import \
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

    category_breakdown_uc = ComputeCategoryBreakdownUseCase()
    print(spliced_transactions, flush=True)
    breakdown = category_breakdown_uc.execute(spliced_transactions)
    return jsonify([{
        "category_parent": row.category_parent,
        "total": row.total,
        "nb_operations": row.nb_operations
    } for row in breakdown])


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
