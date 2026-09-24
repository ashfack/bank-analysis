---
title: Bank Analysis
emoji: 📊
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
license: unknown
short_description: Interactive budget analysis and Excel report generation
---

# Bank Analysis

Bank Analysis turns three CSV files—bank transactions, category mappings, and budget
rules—into an interactive Streamlit dashboard and a navigable Excel report.

The application assigns expenses to master clusters, builds financial cycles from salary
transactions, estimates theoretical budgets, reports input inconsistencies, and lets users
drill down from aggregated amounts to the underlying transactions.

## Features

- Upload three CSV files from the Streamlit interface.
- Apply manual mappings or statistically classify banking categories.
- Build financial cycles anchored on the `Salaire fixe` category.
- Select a budget strategy through temporal validation.
- Apply fixed, symbolic, category-level, or cluster-level budget overrides.
- Display budget consumption with consistent status colors.
- Filter results by financial cycle and master cluster.
- Inspect the enriched transaction ledger.
- Generate an Excel workbook with Pilotage, Mapping, and Ledger sheets.
- Navigate from Excel aggregates to their detailed transactions.
- Run non-destructive data-quality checks on every uploaded dataset.

## Local Setup

### Requirements

- Python 3.12 or a compatible version.
- A virtual environment is recommended.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Streamlit Application

```bash
streamlit run app.py
```

Open `http://localhost:8501`, upload the three CSV files in the sidebar, and select
**Synchronize & Optimize**.

### Command-Line Execution

Place the input files at the paths configured in `config/config.py`:

```text
input/export-operations.csv
input/mapping_config.csv
input/budget_config.csv
```

Then run:

```bash
python main.py
```

The generated workbook is written to `output/Budgeted_V1.xlsx`.

## Input Formats

CSV files use `;` as their delimiter and UTF-8 encoding. French-formatted amounts with
decimal commas, spaces, or non-breaking spaces are accepted.

### Bank Transactions

Minimum columns used by the application:

```csv
dateOp;label;amount;category
2026-01-01;Monthly salary;2500,00;Salaire fixe
2026-01-03;Supermarket;-82,40;Alimentation
```

`dateOp` and `amount` are mandatory. The category is resolved through the manual mapping
when available and otherwise passed to the automatic classifier.

### Category Mapping

```csv
category;cluster
Salaire fixe;0. Incoming
Alimentation;2. Food
Carburant;10. Carburant
```

A category may appear only once. Duplicate mappings stop the analysis with an explicit
error instead of silently selecting one value.

### Budget Configuration

```csv
category;budget_override
2. Food;600
10. Carburant;120
4. Other Recurring;+10%
```

The `category` column may target either a banking category or an entire master cluster.
Supported rules include:

- `600`: fixed absolute budget;
- `+10%` or `-10%`: relative adjustment;
- `50%`: fraction of the calculated budget;
- `+50` or `-20`: absolute adjustment.

Blank lines and comments beginning with `#` are ignored.

## Data-Quality Checks

After each analysis, a collapsed panel reports:

- strictly identical transaction rows;
- categories without a manual mapping that were classified automatically;
- budget entries that match neither a transaction category nor a master cluster.

These checks are non-destructive: transactions are never removed automatically. Invalid
schemas, duplicate mappings, and unreadable CSV configurations stop the analysis with an
explicit error.

## Architecture

The project uses a layered architecture with inward-facing dependencies. Presentation and
infrastructure depend on the application and domain layers, never the other way around.

```text
Streamlit / CLI
       │
       ▼
AnalysisService ──────── Ports
       │                  ▲
       ▼                  │
  Orchestrator       CSV / Excel adapters
       │
       ├── CycleAssigner
       ├── CategoryAnalyzer
       ├── BudgetAllocator
       └── BudgetViewBuilder
```

### Directory Responsibilities

```text
application/       Use case, analysis result, ports, and cross-file quality rules
domain/            Business services independent from presentation libraries
model/             Immutable contracts and domain types
infrastructure/    Specialized CSV readers and in-memory Excel writer
presentation/      Streamlit components, session state, sidebar, and pages
reporting/         Presentation-neutral table projections shared by UI and Excel
report_generator/  Excel workbook writing, formatting, and internal links
budgeter/          Budget rules, statuses, and extensible strategy registry
categorizer/       Category-classification policy
auto_tuner/        Temporal validation and strategy selection
```

`app.py`, `analysis_runner.py`, and `orchestrator.py` are composition or coordination
points. Detailed calculations live in specialized, independently tested components.

## Analysis Flow

1. The input adapters validate and convert the three CSV files.
2. `CycleAssigner` attaches each transaction to the latest salary cycle or to `Initial`.
3. `CategoryAnalyzer` aggregates history and calculates category statistics.
4. The categorizer applies manual mappings first, then automatic classification rules.
5. The tuner reserves the most recent cycles to evaluate candidate strategies.
6. `BudgetAllocator` applies category-level and cluster-level rules.
7. `BudgetViewBuilder` creates the matrix consumed by every presentation.
8. `DataQualityService` evaluates consistency across all three inputs.
9. Streamlit and Excel consume the same reporting projections.

## Budget Strategies

The built-in strategies are:

- `PERCENTILE_GUARDRAIL`;
- `ADAPTIVE_Z_SCORE`;
- `HISTOGRAM_MODE`;
- `VARIANCE_BUFFER`;
- `HYBRID_VOLATILITY`.

The strategy engine follows an extensible registry model. An additional calculator can be
registered through `StrategyRegistry.register(...)` without changing the main execution
path.

The tuner returns a pure `TuningResult` containing the selected strategy, its configuration,
and the candidate leaderboard. It does not print directly to the console or UI.

## Excel Report

The generated workbook contains:

- **📑 Pilotage**: theoretical budgets and consumption by cycle and cluster;
- **🔍 AI Mapping**: metrics and selected cluster for every category;
- **📝 Ledger**: enriched transactions with their cycle and master cluster.

Streamlit and Excel use the same budget-status rule, ensuring that colors have identical
meaning in both outputs. Pilotage cells can link directly to their corresponding Ledger
rows.

## Hugging Face Deployment and Isolation

The Space uses the Docker SDK and listens on port `7860`.

```bash
docker build -t bank-analysis .
docker run --rm -p 7860:7860 bank-analysis
```

For the Streamlit upload path:

- uploaded files are parsed in memory;
- the Excel workbook is generated in a `BytesIO` buffer;
- user financial data is not written to a shared directory;
- each Streamlit session stores its own result;
- `/tmp` is not required to run an analysis or generate a report.

The Dockerfile runs the complete test suite during the image build. A failing test prevents
the Space image from being deployed.

Personal banking exports must not be committed. `input/export-operations.csv` is excluded
from Git.

## Tests and Quality

The current suite contains 85 tests covering domain units, orchestration, adapters, Excel
generation, the Streamlit interface, and the complete uploaded-file workflow.

```bash
pytest tests/
```

Run with coverage:

```bash
pytest --cov=. --cov-report=term-missing tests/
```

Verified status after the SOLID refactoring:

- 85 tests passing;
- 96% overall coverage;
- 100% coverage for the application service, domain services, orchestrator, models,
  reporting projections, and Excel generator;
- an integration test covering CSV input, analysis, quality checks, and Excel generation;
- Streamlit integration tests covering Pilotage, quality alerts, and the Ledger.

## Extending the Application

- Add or change a business rule in `domain/`.
- Support a new input source by implementing the ports in `application/ports.py`.
- Support a new report format by implementing `ReportWriter`.
- Add a strategy by registering a calculator in `StrategyRegistry`.
- Add a Streamlit page in `presentation/pages.py`.
- Add a shared table representation in `reporting/projections.py`.

Every change should keep both the uploaded-pipeline integration test and the Streamlit
interface tests passing.
