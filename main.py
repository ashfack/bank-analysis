from pathlib import Path

from analysis_runner import run_uploaded_analysis
from config.config import BUDGET_FILE, INPUT_FILE, MAPPING_FILE, OUTPUT_FILE


if __name__ == "__main__":
    result = run_uploaded_analysis(
        Path(INPUT_FILE).read_bytes(),
        Path(MAPPING_FILE).read_bytes(),
        Path(BUDGET_FILE).read_bytes(),
    )
    output = Path(OUTPUT_FILE)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(result.report_bytes)
    print("✅ V1 Budget Leaderboard generated.")
