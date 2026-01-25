"""Shared configuration constants for MeriNetWorth application."""

from pathlib import Path

# Base paths
BASE_PATH = Path(__file__).parent.parent
OUTPUT_PATH = BASE_PATH / "output"

# Data paths (modify the period suffix as needed, e.g., '10.25', '06.25')
_DATA_PERIOD = "10.25"
DATA_PATH = BASE_PATH / "data" / _DATA_PERIOD

# Sub-paths within data directory
BANK_PATH = DATA_PATH / "bank"
EQUITY_PATH = DATA_PATH / "Equity"
MF_PATH = DATA_PATH / "MF"
REAL_ESTATE_PATH = DATA_PATH / "real-estate"
OTHER_ASSETS_PATH = DATA_PATH / "others"
FIXED_INCOME_PATH = DATA_PATH / "fixed-income"
PENSION_PATH = DATA_PATH / "pension"

# Static file paths (not period-dependent)
LIABILITIES_FILE_PATH = BASE_PATH / "data" / "liabilities.csv"
REAL_ESTATE_FILE_PATH = REAL_ESTATE_PATH / "properties.csv"
OTHER_ASSETS_FILE_PATH = OTHER_ASSETS_PATH / "others.csv"
FIXED_INCOME_FILE_PATH = FIXED_INCOME_PATH / "term_deposits.csv"
PENSION_FILE_PATH = PENSION_PATH / "pension.csv"

# Output file paths
DATA_FILE = OUTPUT_PATH / "bank_data.json"
EQUITY_FILE = OUTPUT_PATH / "equity_data.json"
NETWORTH_FILE = OUTPUT_PATH / "networth_data.json"
MF_FILE = OUTPUT_PATH / "mf_data.json"
LIABILITIES_FILE = OUTPUT_PATH / "liabilities_data.json"
REAL_ESTATE_FILE = OUTPUT_PATH / "real_estate_data.json"
OTHER_ASSETS_FILE = OUTPUT_PATH / "other_assets_data.json"
FIXED_INCOME_FILE = OUTPUT_PATH / "fixed_income_data.json"
PENSION_FILE = OUTPUT_PATH / "pension_data.json"

# Ensure output directory exists
OUTPUT_PATH.mkdir(exist_ok=True)


def set_data_period(period: str) -> None:
    """Update the data period (e.g., '10.25', '06.25').

    Args:
        period: The period string in MM.YY format
    """
    global _DATA_PERIOD, DATA_PATH, BANK_PATH, EQUITY_PATH, MF_PATH
    global REAL_ESTATE_PATH, OTHER_ASSETS_PATH, FIXED_INCOME_PATH, PENSION_PATH
    global REAL_ESTATE_FILE_PATH, OTHER_ASSETS_FILE_PATH, FIXED_INCOME_FILE_PATH
    global PENSION_FILE_PATH
    _DATA_PERIOD = period
    DATA_PATH = BASE_PATH / "data" / _DATA_PERIOD
    BANK_PATH = DATA_PATH / "bank"
    EQUITY_PATH = DATA_PATH / "Equity"
    MF_PATH = DATA_PATH / "MF"
    REAL_ESTATE_PATH = DATA_PATH / "real-estate"
    OTHER_ASSETS_PATH = DATA_PATH / "others"
    FIXED_INCOME_PATH = DATA_PATH / "fixed-income"
    PENSION_PATH = DATA_PATH / "pension"
    REAL_ESTATE_FILE_PATH = REAL_ESTATE_PATH / "properties.csv"
    OTHER_ASSETS_FILE_PATH = OTHER_ASSETS_PATH / "others.csv"
    FIXED_INCOME_FILE_PATH = FIXED_INCOME_PATH / "term_deposits.csv"
    PENSION_FILE_PATH = PENSION_PATH / "pension.csv"
