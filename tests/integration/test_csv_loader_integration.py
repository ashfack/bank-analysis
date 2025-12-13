import os
from bank_analysis.adapters.csv_file_loader import CsvFileDataLoader
from bank_analysis.adapters.salary_cycle import SalaryCycleGrouper
from bank_analysis.domain.reporting import summary as summarizer

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DEMO = os.path.join(ROOT, "demo.csv")

def test_csv_loader_reads_demo(tmp_path):
    loader = CsvFileDataLoader(base_path=".")
    path = DEMO if os.path.exists(DEMO) else None
    if path is None:
        tmpfile = tmp_path / "sample.csv"
        tmpfile.write_text("dateOp;dateVal;label;category;categoryParent;supplierFound;amount;comment;accountNum;accountLabel;accountbalance\n2024-07-31;2024-07-31;\"CARTE 30/07/24 TOTO\";\"Bien-être\";\"Vie quotidienne\";\"yves\";-49,40;;000;BoursoBank;4425.21\n2024-07-31;2024-07-31;\"VIR INST\";\"Virements reçus\";\"Virements reçus\";\"madame\";266,00;;000;BoursoBank;4425.21\n")
        path = str(tmpfile)
    transactions = loader.load_and_prepare(path)
    assert transactions[0].month is not None
    assert transactions[0].amount is not None
    summary = summarizer.compute_monthly_summary_core(transactions, cycle_grouper=SalaryCycleGrouper(transactions))
    assert len(summary) >=1