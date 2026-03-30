from enum import Enum, auto

from model.models import StrategyConfig


# --- GLOBAL CONFIGURATION ---
ANCHOR_CATEGORY = 'Salaire fixe'
INPUT_FILE = 'input/export-operations.csv'
MAPPING_FILE = 'input/mapping_config.csv'
BUDGET_FILE = 'input/budget_config.csv'
OUTPUT_FILE = 'output/Budgeted_V1.xlsx'


class BudgetStrategy(Enum):
    """Supported mathematical strategies for budget calculation."""
    PERCENTILE_GUARDRAIL = auto()
    ADAPTIVE_Z_SCORE = auto()
    HISTOGRAM_MODE = auto()
    VARIANCE_BUFFER = auto()
    HYBRID_VOLATILITY = auto()
    VOLATILITY_SHOCK_P90 = auto()
    PORTFOLIO_DYNAMICS = auto()


# --- CLASSIFICATION THRESHOLDS ---
# Threshold for Coefficient of Variation (std/median) to distinguish 'Core' from 'Recurring'
CV_STABILITY_THRESHOLD = 0.4
# Minimum frequency (occurrences/cycles) to be considered 'Core' or 'Recurring'
RECURRING_FREQ_THRESHOLD = 0.7
# Minimum frequency to be considered 'Punctual' vs 'Exceptional'
PUNCTUAL_FREQ_THRESHOLD = 0.1


# --- MASTER SWITCHES ---
MANUAL_MODE = False 
ACTIVE_STRATEGY = BudgetStrategy.HYBRID_VOLATILITY
MANUAL_PARAMS = StrategyConfig(percentile_target=80, safety_multiplier=1.15)

# --- DataLoader Config ---
CSV_SEP = ';'
ENCODING = 'utf-8'

# Column names as they appear in your CSV/Excel files
COL_RAW_DATE = 'dateOp'
COL_RAW_AMOUNT = 'amount'
COL_RAW_CATEGORY = 'category'

COL_RAW_CLUSTER = 'cluster'
COL_RAW_OVERRIDE = 'budget_override'

# Domain name (The name used inside the Logic/Orchestrator)
DOMAIN_DATE = 'dateOperation'