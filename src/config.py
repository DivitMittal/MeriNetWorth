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

# Output file paths
DATA_FILE = OUTPUT_PATH / "bank_data.json"
EQUITY_FILE = OUTPUT_PATH / "equity_data.json"
NETWORTH_FILE = OUTPUT_PATH / "networth_data.json"
MF_FILE = OUTPUT_PATH / "mf_data.json"

# Ensure output directory exists
OUTPUT_PATH.mkdir(exist_ok=True)


def set_data_period(period: str) -> None:
    """Update the data period (e.g., '10.25', '06.25').

    Args:
        period: The period string in MM.YY format
    """
    global _DATA_PERIOD, DATA_PATH, BANK_PATH, EQUITY_PATH, MF_PATH
    _DATA_PERIOD = period
    DATA_PATH = BASE_PATH / "data" / _DATA_PERIOD
    BANK_PATH = DATA_PATH / "bank"
    EQUITY_PATH = DATA_PATH / "Equity"
    MF_PATH = DATA_PATH / "MF"
