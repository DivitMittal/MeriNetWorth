"""
Equity Holdings Parsers for CDSL and NSDL Statements
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List
import re


def parse_cdsl_statement(file_path: Path) -> Optional[Dict]:
    """
    Parse CDSL statement (CSV format)

    Args:
        file_path: Path to CDSL CSV file

    Returns:
        Dictionary with account and holdings information, or None on error
    """
    try:
        # Read the header information (first 8 lines)
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [f.readline().strip() for _ in range(8)]

        # Extract metadata
        dp_id = lines[0].split(":")[1].strip() if ":" in lines[0] else ""
        client_id = lines[1].split(":")[1].strip() if ":" in lines[1] else ""
        holder_name = lines[2].split(":")[1].strip() if ":" in lines[2] else ""
        dp_name = lines[3].split(":")[1].strip() if ":" in lines[3] else ""
        statement_date = lines[6].split(":")[1].strip() if ":" in lines[6] else ""

        # Extract total portfolio value
        portfolio_line = lines[7]
        portfolio_value = 0.0
        if "Total Portfolio Value" in portfolio_line:
            # Extract number from "Total Portfolio Value = 2219200.419* ..."
            match = re.search(r"=\s*([\d.]+)", portfolio_line)
            if match:
                portfolio_value = float(match.group(1))

        # Read holdings data (skipping header rows)
        df = pd.read_csv(file_path, skiprows=9)

        # Parse holdings
        holdings = []
        for _, row in df.iterrows():
            try:
                holding = {
                    "isin": str(row["ISIN"]).strip(),
                    "name": str(row["ISIN Name"]).strip(),
                    "quantity": float(row["Balance "]),  # Note the space in column name
                    "last_price": float(row["Last Closing Price "]),
                    "value": float(row["Value"]),
                    "paid_up_value": float(row["Paid Up Value"]),
                }
                holdings.append(holding)
            except Exception as e:
                print(f"  ⚠️  Warning: Skipping row due to parsing error: {e}")
                continue

        return {
            "depository": "CDSL",
            "dp_id": dp_id,
            "client_id": client_id,
            "holder_name": holder_name,
            "dp_name": dp_name,
            "statement_date": statement_date,
            "total_value": portfolio_value,
            "total_holdings": len(holdings),
            "holdings": holdings,
            "source_file": file_path.name,
        }

    except Exception as e:
        print(f"❌ Error parsing CDSL file {file_path.name}: {str(e)}")
        return None


def parse_nsdl_statement(file_path: Path) -> Optional[Dict]:
    """
    Parse NSDL statement (Excel format)

    Args:
        file_path: Path to NSDL Excel file

    Returns:
        Dictionary with account and holdings information, or None on error
    """
    try:
        # NSDL files are typically Excel format
        # Read all sheets to find the main data
        excel_file = pd.ExcelFile(file_path)

        # Try to read the first sheet (usually contains holdings)
        df = pd.read_excel(file_path, sheet_name=0)

        # Try to extract metadata from top rows
        holder_name = ""
        dp_id = ""
        client_id = ""
        statement_date = ""

        # Look for account info in first few rows
        for i in range(min(10, len(df))):
            row_str = " ".join([str(val) for val in df.iloc[i].values if pd.notna(val)])

            # Extract holder name (prefer "First holder" or "Sole Holder", not "DP Name")
            if ("First holder" in row_str or "Sole Holder" in row_str) and not holder_name:
                holder_name = row_str.split(":")[-1].strip() if ":" in row_str else ""
            elif "Holder Name" in row_str and not holder_name:
                holder_name = row_str.split(":")[-1].strip() if ":" in row_str else ""

            # Extract DP ID
            if "DP ID" in row_str and ":" in row_str and not dp_id:
                parts = row_str.split(":")
                if len(parts) >= 2:
                    dp_id = parts[-1].strip()

            # Extract Client ID
            if "Client ID" in row_str and ":" in row_str and not client_id:
                parts = row_str.split(":")
                if len(parts) >= 2:
                    client_id = parts[-1].strip()

            # Extract statement date
            if "as on" in row_str.lower() and not statement_date:
                # Extract date from format like "SOH as on 21-Oct-2025 at 15:59:24"
                if "at" in row_str:
                    # Get text between "as on" and "at"
                    date_part = row_str.lower().split("as on")[-1].split("at")[0].strip()
                    statement_date = date_part
                else:
                    statement_date = row_str.split(":")[-1].strip() if ":" in row_str else ""

        # Combine DP ID and Client ID for account number
        account_number = (dp_id + client_id) if dp_id or client_id else ""

        # Find the header row (contains "ISIN" or "Security Name" or similar keywords)
        header_row = None
        header_keywords = ['isin', 'security name', 'scrip name', 'security', 'scrip',
                          'quantity', 'balance', 'holding', 'instrument']

        for i in range(min(20, len(df))):
            row_str = " ".join([str(val) for val in df.iloc[i].values if pd.notna(val)]).lower()

            # Check if row contains multiple header keywords (likely a header row)
            keyword_matches = sum(1 for keyword in header_keywords if keyword in row_str)
            if keyword_matches >= 2:  # At least 2 keywords suggest this is a header row
                header_row = i
                break

        if header_row is None:
            # Fallback: try to find any row with "ISIN" alone
            for i in range(min(20, len(df))):
                row_str = " ".join([str(val) for val in df.iloc[i].values if pd.notna(val)]).lower()
                if 'isin' in row_str:
                    header_row = i
                    break

        if header_row is None:
            print(f"⚠️  Warning: Could not find header row in {file_path.name}")
            print(f"   Showing first 5 rows for debugging:")
            for i in range(min(5, len(df))):
                print(f"   Row {i}: {df.iloc[i].values}")
            return None

        # Re-read with correct header
        # Note: header_row is the index in the DataFrame (which already consumed row 0 as header)
        # So we need to skip header_row + 1 rows from the raw Excel file
        df = pd.read_excel(file_path, sheet_name=0, skiprows=header_row + 1)

        # Find relevant columns (column names may vary)
        isin_col = None
        name_col = None
        qty_col = None

        # More flexible column matching with expanded keywords
        # Clean column names: strip whitespace and remove special chars
        for col in df.columns:
            # Handle unnamed columns
            if str(col).startswith('Unnamed'):
                continue

            col_lower = str(col).lower().strip().replace('\n', ' ').replace('\r', ' ')

            # ISIN column - expanded keywords
            isin_keywords = ['isin', 'isin no', 'isin number', 'code', 'symbol',
                           'scrip code', 'security code', 'sec code']
            if not isin_col and any(keyword in col_lower for keyword in isin_keywords):
                isin_col = col

            # Name column - expanded keywords
            name_keywords = ['name', 'security', 'scrip', 'description', 'instrument',
                           'security name', 'scrip name', 'name of security',
                           'sec name', 'company', 'company name']
            if not name_col and any(keyword in col_lower for keyword in name_keywords):
                name_col = col

            # Quantity column - expanded keywords
            qty_keywords = ['quantity', 'balance', 'holding', 'unit', 'qty', 'shares',
                          'bal qty', 'bal.qty', 'bal', 'free qty', 'total qty',
                          'no. of shares', 'no.of shares', 'no of shares',
                          'closing balance', 'closing bal']
            if not qty_col and any(keyword in col_lower for keyword in qty_keywords):
                qty_col = col

        if not (isin_col and name_col and qty_col):
            print(f"⚠️  Warning: Could not identify all required columns in {file_path.name}")
            print(f"   Available columns: {df.columns.tolist()}")
            print(f"   Found - ISIN: {isin_col}, Name: {name_col}, Qty: {qty_col}")

            # Smarter fallback strategy
            # 1. Try to use positional logic if we got at least one column
            if len(df.columns) >= 3:
                print(f"   Attempting intelligent fallback based on column positions")

                # If we found name but not ISIN, ISIN is likely the column before name
                if name_col and not isin_col:
                    name_idx = df.columns.get_loc(name_col)
                    if name_idx > 0:
                        isin_col = df.columns[name_idx - 1]
                        print(f"      Guessing ISIN column: {isin_col}")

                # If we found name but not qty, qty is likely the column after name
                if name_col and not qty_col:
                    name_idx = df.columns.get_loc(name_col)
                    if name_idx < len(df.columns) - 1:
                        # Try next few columns for numeric data
                        for offset in range(1, min(4, len(df.columns) - name_idx)):
                            test_col = df.columns[name_idx + offset]
                            # Check if column has numeric data
                            if pd.api.types.is_numeric_dtype(df[test_col]) or df[test_col].dtype == 'object':
                                try:
                                    # Try to convert first non-null value to float
                                    first_val = df[test_col].dropna().iloc[0] if len(df[test_col].dropna()) > 0 else None
                                    if first_val is not None and float(first_val) > 0:
                                        qty_col = test_col
                                        print(f"      Guessing Qty column: {qty_col}")
                                        break
                                except:
                                    continue

                # Last resort: use first 3 non-unnamed columns
                if not (isin_col and name_col and qty_col):
                    non_unnamed = [col for col in df.columns if not str(col).startswith('Unnamed')]
                    if len(non_unnamed) >= 3:
                        print(f"      Using first 3 non-unnamed columns")
                        isin_col = non_unnamed[0]
                        name_col = non_unnamed[1]
                        qty_col = non_unnamed[2]
                    elif len(df.columns) >= 3:
                        print(f"      Using first 3 columns (including unnamed)")
                        isin_col = df.columns[0]
                        name_col = df.columns[1]
                        qty_col = df.columns[2]
                    else:
                        return None
            else:
                return None

        # Parse holdings
        holdings = []
        for _, row in df.iterrows():
            try:
                isin = str(row[isin_col]).strip()

                # Skip empty rows or summary rows
                if pd.isna(row[isin_col]) or isin == "" or isin.lower() == "nan":
                    continue

                # NSDL statements typically don't have price data
                holding = {
                    "isin": isin,
                    "name": str(row[name_col]).strip(),
                    "quantity": float(row[qty_col]),
                    "last_price": 0.0,  # Will be fetched from API
                    "value": 0.0,  # Will be calculated
                    "paid_up_value": 0.0,
                }
                holdings.append(holding)
            except Exception as e:
                continue

        # Extract account number from filename if not found
        if not account_number:
            # NSDL filenames often have format: 5150801IN30021411722076.xlsx
            account_number = file_path.stem
            # Try to split filename into DP ID (8 chars) and Client ID (rest)
            if not dp_id and len(account_number) >= 8:
                dp_id = account_number[:8]
            if not client_id and len(account_number) > 8:
                client_id = account_number[8:]

        return {
            "depository": "NSDL",
            "dp_id": dp_id if dp_id else (account_number[:8] if len(account_number) >= 8 else account_number),
            "client_id": client_id if client_id else (account_number[8:] if len(account_number) > 8 else ""),
            "holder_name": holder_name,
            "dp_name": "NSDL",
            "statement_date": statement_date,
            "total_value": 0.0,  # Will be calculated after price fetch
            "total_holdings": len(holdings),
            "holdings": holdings,
            "source_file": file_path.name,
        }

    except Exception as e:
        print(f"❌ Error parsing NSDL file {file_path.name}: {str(e)}")
        return None


def consolidate_equity_data(equity_accounts: List[Dict]) -> Dict:
    """
    Consolidate equity data from multiple demat accounts

    Args:
        equity_accounts: List of parsed equity account dictionaries

    Returns:
        Consolidated equity data dictionary
    """
    if not equity_accounts:
        return {
            "total_value": 0.0,
            "total_holdings": 0,
            "total_accounts": 0,
            "depositories": {},
            "accounts": [],
        }

    # Calculate totals
    total_value = sum(acc["total_value"] for acc in equity_accounts)
    total_holdings = sum(acc["total_holdings"] for acc in equity_accounts)

    # Group by depository
    depositories = {"CDSL": 0.0, "NSDL": 0.0}
    for acc in equity_accounts:
        dep = acc["depository"]
        depositories[dep] = depositories.get(dep, 0.0) + acc["total_value"]

    # Consolidate all holdings across accounts
    all_holdings = []
    for acc in equity_accounts:
        for holding in acc["holdings"]:
            all_holdings.append(
                {
                    **holding,
                    "account": f"{acc['depository']}-{acc['client_id']}",
                    "holder_name": acc["holder_name"],
                }
            )

    # Group holdings by ISIN (for consolidated view)
    holdings_by_isin = {}
    for holding in all_holdings:
        isin = holding["isin"]
        if isin not in holdings_by_isin:
            holdings_by_isin[isin] = {
                "isin": isin,
                "name": holding["name"],
                "total_quantity": 0.0,
                "last_price": holding["last_price"],
                "total_value": 0.0,
                "accounts": [],
            }
        holdings_by_isin[isin]["total_quantity"] += holding["quantity"]
        holdings_by_isin[isin]["total_value"] += holding["value"]
        holdings_by_isin[isin]["accounts"].append(
            {
                "account": holding["account"],
                "holder_name": holding["holder_name"],
                "quantity": holding["quantity"],
            }
        )

    consolidated_holdings = list(holdings_by_isin.values())
    # Sort by value descending
    consolidated_holdings.sort(key=lambda x: x["total_value"], reverse=True)

    return {
        "total_value": total_value,
        "total_holdings": total_holdings,
        "total_accounts": len(equity_accounts),
        "depositories": depositories,
        "accounts": equity_accounts,
        "consolidated_holdings": consolidated_holdings,
    }
