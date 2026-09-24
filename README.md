---
title: Bank Analysis
emoji: 👁
colorFrom: pink
colorTo: blue
sdk: docker
pinned: false
license: unknown
short_description: Bank analysis
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference


# 📊 Awesome Budgeter

An automated financial orchestration engine that transforms raw banking transactions into a professional-grade, interactive Excel dashboard. Featuring smart categorization, budget tracking, and deep-link navigation.

## 🚀 Core Features

*   **Smart Categorization**: Automatically maps raw transactions to Master Clusters (Fixed, Variable, Savings, etc.) using a robust mapping engine.
*   **Dynamic Pivot Engine**: Generates time-series spending analysis across financial cycles (Monthly/Bi-weekly).
*   **Interactive Excel Architecture**:
    *   **Clickable Headers**: Jump from the Dashboard directly to the specific cluster logic in the **Mapping** tab.
    *   **Deep-Link Spending**: Click any spending total to view the specific underlying transactions in the **Details** tab.
    *   **Visual Budget Alerts**: Automated heatmap logic (Green/Orange/Red) based on real-time spending vs. theoretical budget thresholds.
*   **Symbolic Overrides**: Support for custom budget logic and manual overrides for specific clusters to handle financial edge cases.

---

## 🏗️ Architecture & Flow

The code is organized around explicit responsibilities and inward-facing dependencies:

1. **Presentation**: Streamlit composition, sidebar, session state and page rendering.
2. **Application**: `AnalysisService` coordinates one analysis through injected ports.
3. **Domain**: Cycle assignment, category analysis, budget allocation and view construction.
4. **Infrastructure**: Specialized CSV readers and the in-memory Excel report writer.
5. **Reporting**: Shared presentation-neutral table projections used by Streamlit and Excel.

Uploaded files and generated workbooks are processed in memory. The application does not
depend on a shared input directory or a persistent `/tmp` workspace, which keeps concurrent
Hugging Face sessions isolated.

---

## 🧪 Testing & Quality Assurance

This project maintains a professional standard of code quality with **95%+ coverage** on core logic files.

### Running Tests
To execute the full test suite (85 tests):
```bash
pytest tests/
```

Coverage Report
To view the detailed line-by-line coverage report:
```bash
pytest --cov=. --cov-report term-missing
```

Current Health Status:

Logic (Models, Budgeting, Categorization): 100% Coverage

Reporting (Excel Architect): 95% Coverage

Orchestration: 91% Coverage

## 🛠️ Installation & Usage
Prerequisites<br/>
    Python 3.12+<br/> 
    Virtual Environment (recommended)

Setup<br/>
- Clone the repository.

- Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
Execution
Run the main orchestrator to generate your report:

```bash
python main.py
```
The output file will be generated at the path specified in your config.py.

## 📋 Technical Stack

- Language: Python 3.12

- Data Analysis: Pandas, NumPy

- Excel Engine: XlsxWriter

- Testing Framework: Pytest, Pytest-Cov

- Contracts: Typed immutable dataclasses and protocol-based application ports



## 🖼️ Dashboard Layout

The generated Pilotage sheet is structured for maximum clarity:

Row 0: Interactive Cluster Headers (Hyperlinks to Mapping tab).

Row 1: BUDGET THEORIQUE (Blue-italicized reference line for spending limits).

Row 2+: Time-series spend data with integrated heatmap colors and deep-links to transaction details.

Note: This project was developed with a focus on Test-Driven Development (TDD), ensuring that every financial calculation is verified by the test suite before it ever reaches the final spreadsheet.
