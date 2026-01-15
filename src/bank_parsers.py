import pandas as pd
from pathlib import Path
from typing import Dict, Optional


def clean_amount(value) -> float:
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = str(value).replace("₹", "").replace(",", "").replace("INR", "").strip()
    try:
        return float(cleaned)
    except:
        return 0.0


def extract_account_number(text) -> str:
    if pd.isna(text):
        return ""
    return str(text).strip()


def standardize_holder_name(name) -> str:
    if pd.isna(name):
        return ""
    name = str(name).strip()
    replacements = {"Mrs.": "", "Mr.": "", "Ms.": "", "MITAL": "Mittal", "MITTAL": "Mittal"}
    for old, new in replacements.items():
        name = name.replace(old, new)
    return name.strip()


def parse_idfc_statement(file_path: Path) -> Optional[Dict]:
    try:
        df = pd.read_excel(file_path, sheet_name="Account Statement")

        account_number = ""
        holder_name = ""
        closing_balance = 0.0

        for idx, row in df.iterrows():
            if "ACCOUNT NUMBER" in str(row[0]):
                account_number = extract_account_number(row[1])
            elif "CUSTOMER NAME" in str(row[0]):
                holder_name = standardize_holder_name(row[1])
            elif "Opening Balance" in str(row[0]) and "Closing Balance" in str(row[3]):
                if idx + 1 < len(df):
                    closing_balance = clean_amount(df.iloc[idx + 1][3])
                    break

        return {
            "bank": "IDFC FIRST",
            "account_number": account_number,
            "holder_name": holder_name,
            "first_holder": holder_name,
            "second_holder": "",
            "nominee": "",
            "balance": closing_balance,
            "source_file": file_path.name,
        }
    except Exception as e:
        print(f"Error parsing IDFC file {file_path.name}: {str(e)}")
        return None


def parse_equitas_statement(file_path: Path) -> Optional[Dict]:
    try:
        df = pd.read_excel(file_path, sheet_name=0)

        account_number = ""
        holder_name = ""
        nominee_name = ""
        joint_holders = []
        closing_balance = 0.0

        for idx, row in df.iterrows():
            if "Account Number" in str(row.iloc[4]):
                account_number = extract_account_number(row.iloc[5])
            elif "Customer Name" in str(row.iloc[1]):
                holder_name = standardize_holder_name(row.iloc[2])
            elif "Nominee Name" in str(row.iloc[1]):
                nominee_name = standardize_holder_name(row.iloc[2])
            elif "Joint Holder" in str(row.iloc[1]):
                joint_text = str(row.iloc[2])
                if pd.notna(row.iloc[2]) and joint_text.strip():
                    joint_holders = [standardize_holder_name(h.strip()) for h in joint_text.split('\n') if h.strip()]
            elif "Available Balance" in str(row.iloc[4]):
                closing_balance = clean_amount(row.iloc[5])

        if closing_balance == 0.0:
            for idx in range(len(df) - 1, -1, -1):
                if "End of the Statement" not in str(df.iloc[idx, 0]):
                    last_balance = clean_amount(df.iloc[idx, -1])
                    if last_balance > 0:
                        closing_balance = last_balance
                        break

        first_holder = holder_name
        second_holder = ""
        if len(joint_holders) >= 2:
            first_holder = joint_holders[0]
            second_holder = joint_holders[1]
        elif len(joint_holders) == 1:
            first_holder = joint_holders[0]

        return {
            "bank": "Equitas",
            "account_number": account_number,
            "holder_name": holder_name,
            "first_holder": first_holder,
            "second_holder": second_holder,
            "nominee": nominee_name,
            "balance": closing_balance,
            "source_file": file_path.name,
        }
    except Exception as e:
        print(f"Error parsing Equitas file {file_path.name}: {str(e)}")
        return None


def parse_bandhan_statement(file_path: Path) -> Optional[Dict]:
    try:
        df = pd.read_csv(file_path)

        closing_balance = 0.0
        balance_cols = [col for col in df.columns if "balance" in col.lower()]
        if balance_cols:
            closing_balance = clean_amount(df[balance_cols[0]].iloc[-1])

        return {
            "bank": "Bandhan",
            "account_number": file_path.stem,
            "holder_name": "",
            "first_holder": "",
            "second_holder": "",
            "nominee": "",
            "balance": closing_balance,
            "source_file": file_path.name,
        }
    except Exception as e:
        print(f"Error parsing Bandhan file {file_path.name}: {str(e)}")
        return None


def parse_icici_statement(file_path: Path) -> Optional[Dict]:
    try:
        df_raw = pd.read_excel(file_path, header=None)

        closing_balance = 0.0
        account_number = ""
        holder_name = ""
        first_holder = ""
        second_holder = ""

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

        for idx, row in df_raw.iterrows():
            if idx >= header_row_idx:
                break

            for col_idx, val in enumerate(row):
                if pd.notna(val) and "Account Number" in str(val):
                    if col_idx + 1 < len(row):
                        account_info = str(row[col_idx + 1])
                        if " - " in account_info:
                            parts = account_info.split(" - ")
                            account_number = extract_account_number(parts[0].split("(")[0].strip())
                            if len(parts) > 1:
                                holder_name = standardize_holder_name(parts[1].strip())

            for val in row:
                if pd.notna(val) and "Transactions List" in str(val):
                    text = str(val)
                    parts = text.split(" - ")
                    if len(parts) >= 2:
                        names_part = parts[1].strip()
                        if "," in names_part:
                            names = [n.strip() for n in names_part.split(",")]
                            first_holder = standardize_holder_name(names[0])
                            if len(names) > 1:
                                second_holder = standardize_holder_name(names[1])
                        else:
                            first_holder = standardize_holder_name(names_part)

                        if not holder_name:
                            holder_name = first_holder

                        if len(parts) >= 3 and not account_number:
                            account_number = extract_account_number(parts[2].strip())

        if header_row_idx is not None and balance_col_idx is not None:
            balance_values = df_raw[balance_col_idx].iloc[header_row_idx + 1 :].dropna()
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

        if not account_number:
            account_number = file_path.stem

        return {
            "bank": "ICICI",
            "account_number": account_number,
            "holder_name": holder_name,
            "first_holder": first_holder,
            "second_holder": second_holder,
            "nominee": "",
            "balance": closing_balance,
            "source_file": file_path.name,
        }
    except Exception as e:
        print(f"Error parsing ICICI file {file_path.name}: {str(e)}")
        return None


def parse_indusind_statement(file_path: Path) -> Optional[Dict]:
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
            "first_holder": "",
            "second_holder": "",
            "nominee": "",
            "balance": closing_balance,
            "source_file": file_path.name,
        }
    except Exception as e:
        print(f"Error parsing IndusInd file {file_path.name}: {str(e)}")
        return None


def parse_kotak_statement(file_path: Path) -> Optional[Dict]:
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()

        account_number = ""
        holder_name = ""
        nominee_name = ""
        joint_holders = []
        closing_balance = 0.0
        transaction_start_idx = -1

        for i, line in enumerate(lines):
            if i == 1:
                holder_name = standardize_holder_name(line.strip())

            if "Account No." in line:
                parts = line.split(',')
                for j, part in enumerate(parts):
                    if "Account No." in part and j + 1 < len(parts):
                        account_number = extract_account_number(parts[j + 1].strip())
                        break

            if "Nominee Name" in line:
                parts = line.split(',')
                for j, part in enumerate(parts):
                    if "Nominee Name" in part and j + 1 < len(parts):
                        nominee_name = standardize_holder_name(parts[j + 1].strip())
                        break

            if "Joint Holder" in line:
                parts = line.split(',')
                for j, part in enumerate(parts):
                    if "Joint Holder" in part and j + 1 < len(parts):
                        joint_text = parts[j + 1].strip()
                        if joint_text:
                            joint_holders.append(standardize_holder_name(joint_text))
                        break

            if "Sl. No." in line and "Transaction Date" in line:
                transaction_start_idx = i + 1
                break

        if transaction_start_idx > 0:
            df_transactions = pd.read_csv(file_path, skiprows=transaction_start_idx - 1)

            balance_col = None
            for col in df_transactions.columns:
                if "Balance" in str(col):
                    balance_col = col
                    break

            if balance_col is not None:
                balance_values = df_transactions[balance_col].dropna()
                if len(balance_values) > 0:
                    closing_balance = clean_amount(balance_values.iloc[-1])

        first_holder = holder_name
        second_holder = ""
        if len(joint_holders) >= 1:
            second_holder = joint_holders[0]

        return {
            "bank": "Kotak Mahindra",
            "account_number": account_number,
            "holder_name": holder_name,
            "first_holder": first_holder,
            "second_holder": second_holder,
            "nominee": nominee_name,
            "balance": closing_balance,
            "source_file": file_path.name,
        }
    except Exception as e:
        print(f"Error parsing Kotak file {file_path.name}: {str(e)}")
        return None


PARSERS = {
    "idfc": parse_idfc_statement,
    "equitas": parse_equitas_statement,
    "bandhan": parse_bandhan_statement,
    "icici": parse_icici_statement,
    "indusind": parse_indusind_statement,
    "kotak": parse_kotak_statement,
}


def get_parser(bank_name: str):
    return PARSERS.get(bank_name.lower())
