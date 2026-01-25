"""Liability parser for MeriNetWorth."""

from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from .config import LIABILITIES_FILE, LIABILITIES_FILE_PATH
from .utils import clean_amount, save_json


def parse_liability_file(file_path: Path) -> Optional[dict]:
    """Parse a liability CSV file.

    Expected CSV format:
    - Date: Date of transaction
    - Beneficiary: Description of the liability
    - Amount (INR): Amount in INR (negative = owed, positive = received/paid)
    - Amount (Euro): Optional Euro amount
    - Exchange Rate: Optional exchange rate

    Args:
        file_path: Path to the liability CSV file

    Returns:
        Dict with liability info or None on error
    """
    try:
        df = pd.read_csv(file_path, encoding="utf-8-sig")

        liabilities = []
        total_amount = 0.0

        for _, row in df.iterrows():
            beneficiary = row.get("Beneficiary", "")
            if pd.isna(beneficiary) or str(beneficiary).strip() == "":
                continue
            if "TOTAL" in str(beneficiary).upper():
                continue

            amount_inr = clean_amount(row.get("Amount (INR)", 0))
            amount_euro = clean_amount(row.get("Amount (Euro)", 0))
            exchange_rate = clean_amount(row.get("Exchange Rate", 0))

            date_str = str(row.get("Date", "")).strip()
            parsed_date = None
            if date_str and not pd.isna(row.get("Date")):
                try:
                    parsed_date = pd.to_datetime(date_str).strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    parsed_date = date_str

            liability = {
                "date": parsed_date,
                "beneficiary": str(beneficiary).strip(),
                "amount_inr": amount_inr,
                "amount_euro": amount_euro if amount_euro != 0 else None,
                "exchange_rate": exchange_rate if exchange_rate != 0 else None,
            }
            liabilities.append(liability)
            total_amount += amount_inr

        # The total is typically negative (money owed)
        # We want total_liabilities to be positive for display
        net_liability = abs(total_amount) if total_amount < 0 else 0
        net_receivable = total_amount if total_amount > 0 else 0

        return {
            "source_file": file_path.name,
            "transactions": liabilities,
            "total_amount": total_amount,
            "net_liability": net_liability,
            "net_receivable": net_receivable,
            "transaction_count": len(liabilities),
        }

    except Exception as e:
        print(f"Error parsing liability file {file_path.name}: {e}")
        return None


def process_all_liabilities() -> dict:
    """Process liability data from the liabilities CSV file.

    Returns:
        Dict containing all liabilities data
    """
    all_liabilities = []
    total_liability = 0.0
    total_receivable = 0.0

    if not LIABILITIES_FILE_PATH.exists():
        print(f"Liabilities file not found: {LIABILITIES_FILE_PATH}")
        return {
            "generated_at": datetime.now().isoformat(),
            "liabilities": [],
            "total_liability": 0.0,
            "total_receivable": 0.0,
            "net_position": 0.0,
        }

    print("\n📋 Processing Liabilities...")

    result = parse_liability_file(LIABILITIES_FILE_PATH)
    if result:
        all_liabilities.append(result)
        total_liability += result["net_liability"]
        total_receivable += result["net_receivable"]
        print(f"  ✓ {LIABILITIES_FILE_PATH.name}: Net liability ₹{result['net_liability']:,.2f}")

    net_position = total_receivable - total_liability

    data = {
        "generated_at": datetime.now().isoformat(),
        "liabilities": all_liabilities,
        "total_liability": total_liability,
        "total_receivable": total_receivable,
        "net_position": net_position,
    }

    print(f"\n📊 Total Liability: ₹{total_liability:,.2f}")
    print(f"📊 Total Receivable: ₹{total_receivable:,.2f}")
    print(f"📊 Net Position: ₹{net_position:,.2f}")

    return data


def save_liabilities_json(data: dict) -> Path:
    """Save liabilities data to JSON file.

    Args:
        data: Liabilities data dict

    Returns:
        Path to the saved file
    """
    return save_json(data, LIABILITIES_FILE, "Liabilities")
