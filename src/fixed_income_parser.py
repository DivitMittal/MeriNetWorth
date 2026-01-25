"""Parser for fixed income assets (term deposits, FDs)."""

from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from .config import FIXED_INCOME_FILE_PATH, OUTPUT_PATH
from .utils import clean_amount, save_json


def clean_rate(value) -> float:
    """Clean and convert interest rate to float."""
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = str(value).replace("%", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def parse_date(value) -> Optional[str]:
    """Parse date string to ISO format."""
    if pd.isna(value) or str(value).strip() == "":
        return None
    try:
        # Try common formats
        for fmt in ["%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%b-%Y"]:
            try:
                return datetime.strptime(str(value).strip(), fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return str(value).strip()
    except Exception:
        return str(value).strip()


def parse_fixed_income_file(file_path: Path) -> Optional[dict]:
    """Parse a fixed income CSV file.

    Expected CSV columns:
    - S.No, Bank, FD Number, Amount, Inception Date, Maturity Date,
    - Maturity Instruction, Holders, Nomination, Interest rate,
    - Physical Copy, Online Access, Quarterly, Interest Payout

    Args:
        file_path: Path to the fixed income CSV file

    Returns:
        Dict with fixed income info or None on error
    """
    try:
        df = pd.read_csv(file_path, encoding="utf-8-sig")
        df.columns = df.columns.str.strip()

        deposits = []
        total_principal = 0.0
        total_quarterly_interest = 0.0

        for _, row in df.iterrows():
            fd_number = row.get("FD Number", "")
            if pd.isna(fd_number) or str(fd_number).strip() == "":
                continue

            amount = clean_amount(row.get("Amount", 0))
            interest_rate = clean_rate(row.get("Interest rate", 0))
            quarterly_interest = clean_amount(row.get("Quarterly", 0))

            deposit = {
                "bank": str(row.get("Bank", "")).strip(),
                "fd_number": str(fd_number).strip(),
                "amount": amount,
                "inception_date": parse_date(row.get("Inception Date")),
                "maturity_date": parse_date(row.get("Maturity Date")),
                "maturity_instruction": str(row.get("Maturity Instruction", "")).strip(),
                "holders": str(row.get("Holders", "")).strip(),
                "nomination": str(row.get("Nomination", "")).strip(),
                "interest_rate": interest_rate,
                "quarterly_interest": quarterly_interest,
                "interest_payout": str(row.get("Interest Payout", "")).strip(),
            }
            deposits.append(deposit)
            total_principal += amount
            total_quarterly_interest += quarterly_interest

        return {
            "source_file": file_path.name,
            "deposits": deposits,
            "total_principal": total_principal,
            "total_quarterly_interest": total_quarterly_interest,
            "annual_interest_estimate": total_quarterly_interest * 4,
            "deposit_count": len(deposits),
        }

    except Exception as e:
        print(f"Error parsing fixed income file {file_path.name}: {e}")
        return None


def process_fixed_income() -> dict:
    """Process fixed income data from CSV file.

    Returns:
        Dict containing fixed income data
    """
    if not FIXED_INCOME_FILE_PATH.exists():
        print(f"Fixed income file not found: {FIXED_INCOME_FILE_PATH}")
        return {
            "generated_at": datetime.now().isoformat(),
            "deposits": [],
            "total_principal": 0.0,
            "total_quarterly_interest": 0.0,
            "annual_interest_estimate": 0.0,
            "by_bank": {},
        }

    print("\n💰 Processing Fixed Income (Term Deposits)...")

    result = parse_fixed_income_file(FIXED_INCOME_FILE_PATH)
    if result:
        print(f"  ✓ {FIXED_INCOME_FILE_PATH.name}: {result['deposit_count']} deposits")
        print(f"    Total Principal: ₹{result['total_principal']:,.2f}")
        print(f"    Quarterly Interest: ₹{result['total_quarterly_interest']:,.2f}")

        # Aggregate by bank
        by_bank = {}
        for deposit in result["deposits"]:
            bank = deposit["bank"]
            if bank not in by_bank:
                by_bank[bank] = {"principal": 0.0, "quarterly_interest": 0.0, "count": 0}
            by_bank[bank]["principal"] += deposit["amount"]
            by_bank[bank]["quarterly_interest"] += deposit["quarterly_interest"]
            by_bank[bank]["count"] += 1

        for bank, data in by_bank.items():
            print(f"    - {bank}: ₹{data['principal']:,.2f} ({data['count']} FDs)")

        return {
            "generated_at": datetime.now().isoformat(),
            "deposits": result["deposits"],
            "total_principal": result["total_principal"],
            "total_quarterly_interest": result["total_quarterly_interest"],
            "annual_interest_estimate": result["annual_interest_estimate"],
            "deposit_count": result["deposit_count"],
            "by_bank": by_bank,
            "source_file": result["source_file"],
        }

    return {
        "generated_at": datetime.now().isoformat(),
        "deposits": [],
        "total_principal": 0.0,
        "total_quarterly_interest": 0.0,
        "annual_interest_estimate": 0.0,
        "by_bank": {},
    }


def save_fixed_income_json(data: dict) -> Path:
    """Save fixed income data to JSON file."""
    return save_json(data, OUTPUT_PATH / "fixed_income_data.json", "Fixed income")
