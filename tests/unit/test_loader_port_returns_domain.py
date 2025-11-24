import csv
from pathlib import Path
from bank_analysis.adapters.csv_file_loader import CsvFileDataLoader

def test_loader_returns_domain_transactions(tmp_path: Path):
    p = tmp_path / "txns.csv"
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["dateOp", "month", "category", "categoryParent", "amount"])
        w.writeheader()
        w.writerow({"dateOp":"2025-01-25","month":"2025-01","category":"Salaire fixe","categoryParent":"Income","amount":"3 700"})
        w.writerow({"dateOp":"2025-01-10","month":"2025-01","category":"Groceries","categoryParent":"Essentials","amount":"-150,50"})

    txns = CsvFileDataLoader().load_and_prepare(str(p))
    assert len(txns) == 2
    assert txns[0].amount == 3700.0
    assert txns[1].amount == -150.50
