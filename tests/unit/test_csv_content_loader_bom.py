from bank_analysis.adapters.csv_content_loader import CsvContentDataLoader

def test_bom_in_header_is_handled():
    # Note the BOM (\ufeff) prefix on the first header
    csv_text = "\ufeffdateOp;month;category;categoryParent;amount;supplierFound;label\n2025-11-20;2025-11;Food;Essentials;-21,70;Yves Rocher;JOJO\n"
    loader = CsvContentDataLoader()
    txns = loader.load_and_prepare(csv_text)
    assert len(txns) == 1
    assert txns[0].month == "2025-11"
    assert txns[0].amount == -21.70
    assert txns[0].category == "Food"
    assert txns[0].category_parent == "Essentials"
    assert txns[0].supplier == "Yves Rocher"
    assert txns[0].message == "JOJO"
