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
            # Header row format: Opening Balance | Total Debit | Total Credit | Closing Balance
            elif "Opening Balance" in str(row[0]) and "Closing Balance" in str(row[3]):
                # Next row has the actual values
                if idx + 1 < len(df):
                    closing_balance = clean_amount(df.iloc[idx + 1][3])
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
        # ICICI files have headers at varying positions, need to find them
        df_raw = pd.read_excel(file_path, header=None)

        closing_balance = 0.0
        account_number = file_path.stem
        holder_name = ""

        # Find the header row with "Balance"
        header_row_idx = None
        balance_col_idx = None

        for idx, row in df_raw.iterrows():
            for col_idx, val in enumerate(row):
                if pd.notna(val) and "Balance(INR)" in str(val):
                    header_row_idx = idx
                    balance_col_idx = col_idx
                    break
            if header_row_idx is not None:
                break

        # Extract holder name from header (usually in row with "Transactions List")
        for idx, row in df_raw.iterrows():
            if idx >= header_row_idx:
                break
            for val in row:
                if pd.notna(val) and "Transactions List" in str(val):
                    # Format: "Transactions List - NAME1, NAME2 - ACCOUNT"
                    parts = str(val).split("-")
                    if len(parts) >= 2:
                        holder_name = standardize_holder_name(parts[1].strip().split(",")[0])
                    break

        # Get balance from the last transaction row
        if header_row_idx is not None and balance_col_idx is not None:
            # Read transaction data starting after header
            balance_values = df_raw[balance_col_idx].iloc[header_row_idx + 1 :].dropna()
            # Filter out non-numeric values (like "Balance(INR)" if it appears)
            numeric_balances = []
            for val in balance_values:
                try:
                    numeric_val = clean_amount(val)
                    if numeric_val > 0:
                        numeric_balances.append(numeric_val)
                except:
                    pass

            if numeric_balances:
                closing_balance = numeric_balances[-1]

        return {
            "bank": "ICICI",
            "account_number": account_number,
            "holder_name": holder_name,
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


def parse_kotak_statement(file_path: Path) -> Optional[Dict]:
    """
    Parse Kotak Mahindra Bank CSV statement

    Args:
        file_path: Path to Kotak CSV statement file

    Returns:
        Dictionary with account details or None if parsing fails
    """
    try:
        # Read the file as text first to parse header information
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()

        account_number = ""
        holder_name = ""
        closing_balance = 0.0
        transaction_start_idx = -1

        # Parse header lines
        for i, line in enumerate(lines):
            # Holder name is typically in line 1 (index 1)
            if i == 1:
                holder_name = standardize_holder_name(line.strip())

            # Account number is in a line with "Account No."
            if "Account No." in line:
                parts = line.split(',')
                for part in parts:
                    if part.strip() and "Account No." not in part and part.strip() != "":
                        account_number = extract_account_number(part)
                        break

            # Find where transaction table starts
            if "Sl. No." in line and "Transaction Date" in line:
                transaction_start_idx = i + 1
                break

        # Read transaction data from the transaction start line
        if transaction_start_idx > 0:
            # Read CSV starting from transaction table with proper headers
            df_transactions = pd.read_csv(file_path, skiprows=transaction_start_idx - 1)

            # Find balance column
            balance_col = None
            for col in df_transactions.columns:
                if "Balance" in str(col):
                    balance_col = col
                    break

            if balance_col is not None:
                # Get last non-null balance value
                balance_values = df_transactions[balance_col].dropna()
                if len(balance_values) > 0:
                    closing_balance = clean_amount(balance_values.iloc[-1])

        return {
            "bank": "Kotak Mahindra",
            "account_number": account_number,
            "holder_name": holder_name,
            "balance": closing_balance,
            "source_file": file_path.name,
        }
    except Exception as e:
        print(f"❌ Error parsing Kotak file {file_path.name}: {str(e)}")
        return None


# Parser registry for easy access
PARSERS = {
    "idfc": parse_idfc_statement,
    "equitas": parse_equitas_statement,
    "bandhan": parse_bandhan_statement,
    "icici": parse_icici_statement,
    "indusind": parse_indusind_statement,
    "kotak": parse_kotak_statement,
}


def get_parser(bank_name: str):
    """Get parser function for a specific bank"""
    return PARSERS.get(bank_name.lower())
