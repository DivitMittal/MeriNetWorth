"""
Bank Statement Parsers
Reusable parser functions for different bank formats
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Optional


def clean_amount(value) -> float:
    """Convert various amount formats to float"""
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    # Remove currency symbols, commas, and convert to float
    cleaned = str(value).replace("₹", "").replace(",", "").replace("INR", "").strip()
    try:
        return float(cleaned)
    except:
        return 0.0


def extract_account_number(text) -> str:
    """Extract account number from text, handling masked numbers"""
    if pd.isna(text):
        return ""
    return str(text).strip()


def standardize_holder_name(name) -> str:
    """Standardize holder names for consistency"""
    if pd.isna(name):
        return ""
    name = str(name).strip()
    # Common standardizations
    replacements = {"Mrs.": "", "Mr.": "", "Ms.": "", "MITAL": "Mittal", "MITTAL": "Mittal"}
    for old, new in replacements.items():
        name = name.replace(old, new)
    return name.strip()


def parse_idfc_statement(file_path: Path) -> Optional[Dict]:
    """
    Parse IDFC First Bank Excel statement

    Args:
        file_path: Path to IDFC Excel statement file

    Returns:
        Dictionary with account details or None if parsing fails
    """
    try:
        df = pd.read_excel(file_path, sheet_name="Account Statement")

        # Extract account details from header rows
        account_number = ""
        holder_name = ""
        closing_balance = 0.0

        # Find account number (usually in row with 'ACCOUNT NUMBER')
        for idx, row in df.iterrows():
            if "ACCOUNT NUMBER" in str(row[0]):
                account_number = extract_account_number(row[1])
            elif "CUSTOMER NAME" in str(row[0]):
                holder_name = standardize_holder_name(row[1])
            elif "Closing Balance" in str(row[0]):
                closing_balance = clean_amount(row[3])
                break

        return {
            "bank": "IDFC FIRST",
            "account_number": account_number,
            "holder_name": holder_name,
            "balance": closing_balance,
            "source_file": file_path.name,
        }
    except Exception as e:
        print(f"❌ Error parsing IDFC file {file_path.name}: {str(e)}")
        return None


def parse_equitas_statement(file_path: Path) -> Optional[Dict]:
    """
    Parse Equitas Small Finance Bank Excel statement

    Args:
        file_path: Path to Equitas Excel statement file

    Returns:
        Dictionary with account details or None if parsing fails
    """
    try:
        df = pd.read_excel(file_path, sheet_name=0)

        account_number = ""
        holder_name = ""
        closing_balance = 0.0

        # Equitas has a specific structure
        for idx, row in df.iterrows():
            if "Account Number" in str(row[1]):
                account_number = extract_account_number(row[7])
            elif "Customer Name" in str(row[1]):
                holder_name = standardize_holder_name(row[2])
            elif "Available Balance" in str(row[4]):
                closing_balance = clean_amount(row[5])

        # If closing balance not found in header, get from last transaction
        if closing_balance == 0.0:
            for idx in range(len(df) - 1, -1, -1):
                if "End of the Statement" not in str(df.iloc[idx, 0]):
                    last_balance = clean_amount(df.iloc[idx, -1])
                    if last_balance > 0:
                        closing_balance = last_balance
                        break

        return {
            "bank": "Equitas",
            "account_number": account_number,
            "holder_name": holder_name,
            "balance": closing_balance,
            "source_file": file_path.name,
        }
    except Exception as e:
        print(f"❌ Error parsing Equitas file {file_path.name}: {str(e)}")
        return None


def parse_bandhan_statement(file_path: Path) -> Optional[Dict]:
    """
    Parse Bandhan Bank CSV statement

    Args:
        file_path: Path to Bandhan CSV statement file

    Returns:
        Dictionary with account details or None if parsing fails
    """
    try:
        df = pd.read_csv(file_path)

        closing_balance = 0.0

        # Check if 'Balance' or similar column exists
        balance_cols = [col for col in df.columns if "balance" in col.lower()]
        if balance_cols:
            closing_balance = clean_amount(df[balance_cols[0]].iloc[-1])

        return {
            "bank": "Bandhan",
            "account_number": file_path.stem,
            "holder_name": "",
            "balance": closing_balance,
            "source_file": file_path.name,
        }
    except Exception as e:
        print(f"❌ Error parsing Bandhan file {file_path.name}: {str(e)}")
        return None


def parse_icici_statement(file_path: Path) -> Optional[Dict]:
    """
    Parse ICICI Bank XLS statement

    Args:
        file_path: Path to ICICI XLS statement file

    Returns:
        Dictionary with account details or None if parsing fails
    """
    try:
        df = pd.read_excel(file_path)

        closing_balance = 0.0

        # Try to find balance column
        balance_cols = [col for col in df.columns if "balance" in str(col).lower()]
        if balance_cols:
            closing_balance = clean_amount(df[balance_cols[0]].dropna().iloc[-1])

        return {
            "bank": "ICICI",
            "account_number": file_path.stem,
            "holder_name": "",
            "balance": closing_balance,
            "source_file": file_path.name,
        }
    except Exception as e:
        print(f"❌ Error parsing ICICI file {file_path.name}: {str(e)}")
        return None


def parse_indusind_statement(file_path: Path) -> Optional[Dict]:
    """
    Parse IndusInd Bank CSV statement

    Args:
        file_path: Path to IndusInd CSV statement file

    Returns:
        Dictionary with account details or None if parsing fails
    """
    try:
        df = pd.read_csv(file_path)

        closing_balance = 0.0
        balance_cols = [col for col in df.columns if "balance" in col.lower()]

        if balance_cols:
            closing_balance = clean_amount(df[balance_cols[0]].iloc[-1])

        return {
            "bank": "IndusInd",
            "account_number": file_path.stem,
            "holder_name": "",
            "balance": closing_balance,
            "source_file": file_path.name,
        }
    except Exception as e:
        print(f"❌ Error parsing IndusInd file {file_path.name}: {str(e)}")
        return None


# Parser registry for easy access
PARSERS = {
    "idfc": parse_idfc_statement,
    "equitas": parse_equitas_statement,
    "bandhan": parse_bandhan_statement,
    "icici": parse_icici_statement,
    "indusind": parse_indusind_statement,
}


def get_parser(bank_name: str):
    """Get parser function for a specific bank"""
    return PARSERS.get(bank_name.lower())
