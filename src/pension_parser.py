"""Parser for pension assets (NPS, EPF, etc.)."""

from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
import re
import pandas as pd

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

from .config import OUTPUT_PATH, PENSION_FILE_PATH, PENSION_PATH
from .utils import clean_amount, save_json


def parse_nps_pdf(file_path: Path) -> Optional[dict]:
    """Parse NPS statement PDF."""
    if not pdfplumber:
        # Silently fail if library missing, or warn once?
        # Since we just installed it, it should be there.
        print(f"⚠️ pdfplumber not installed. Cannot parse {file_path.name}")
        return None

    try:
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"

            # 1. Extract Name
            # Pattern: "Subscriber Name <Name>"
            # Handling newlines if name is on next line
            name = "Unknown NPS Subscriber"

            # Try single line match
            name_match = re.search(r"Subscriber\s*Name\s*[:\-\s]*([A-Za-z\s\.]+)", text, re.IGNORECASE)
            if name_match:
                candidate = name_match.group(1).strip()
                if candidate and len(candidate) > 2:
                    name = candidate

            # 2. Extract Total Value
            # Strategy: Find "Total" lines in the Scheme Summary tables and sum their last values
            # Rows look like: "Total 10,082.6796 1,90,474.49 1,90,474.49"

            total_value = 0.0
            found_total = False

            for line in text.split('\n'):
                line = line.strip()
                if line.startswith('Total ') or line.startswith('Total\t'):
                    parts = line.split()
                    # Valid total line should have numbers
                    try:
                        # Get the last token that looks like a number
                        # Iterate backwards
                        for part in reversed(parts):
                            # clean_amount handles commas
                            try:
                                val = clean_amount(part)
                                if val > 0:
                                    total_value += val
                                    found_total = True
                                    break # Found the value for this total line
                            except:
                                continue
                    except Exception:
                        pass

            if not found_total:
                print(f"⚠️  Could not find total value in {file_path.name}")

            return {
                "name": name,
                "type": "NPS",
                "value": total_value,
                "source_file": file_path.name
            }

    except Exception as e:
        print(f"Error parsing NPS PDF {file_path.name}: {e}")
        return None


def parse_pension_csv(file_path: Path) -> List[dict]:
    """Parse a pension CSV file."""
    accounts = []
    try:
        df = pd.read_csv(file_path, encoding="utf-8-sig")
        df.columns = df.columns.str.strip()

        for _, row in df.iterrows():
            name = row.get("Name", "")
            if pd.isna(name) or str(name).strip() == "":
                continue

            value = clean_amount(row.get("Current Value", 0))
            pension_type = str(row.get("Type", "NPS")).strip()

            account = {
                "name": str(name).strip(),
                "type": pension_type,
                "value": value,
                "source_file": file_path.name
            }
            accounts.append(account)

    except Exception as e:
        print(f"Error parsing pension CSV {file_path.name}: {e}")

    return accounts


def process_pension() -> dict:
    """Process pension data from CSV and PDFs.

    Returns:
        Dict containing pension data
    """
    all_accounts = []

    print("\n🏦 Processing Pension...")

    # 1. Process CSV if exists (Legacy/Manual)
    if PENSION_FILE_PATH.exists():
        csv_accounts = parse_pension_csv(PENSION_FILE_PATH)
        all_accounts.extend(csv_accounts)

    # 2. Process PDFs (NPS Statements)
    if PENSION_PATH.exists():
        for pdf_file in PENSION_PATH.glob("*.pdf"):
            account = parse_nps_pdf(pdf_file)
            if account:
                # Deduplicate: If same name/type/value exists from CSV, prefer CSV or PDF?
                # For now, just append. Assuming CSV won't contain duplicates of PDF data
                # Or better: check if name/value matches roughly
                all_accounts.append(account)
                print(f"  ✓ {pdf_file.name}: ₹{account['value']:,.2f}")

    if not all_accounts:
        print("  No pension data found.")
        return {
            "generated_at": datetime.now().isoformat(),
            "accounts": [],
            "total_value": 0.0,
            "account_count": 0,
            "by_type": {}
        }

    # Calculate totals
    total_value = sum(acc["value"] for acc in all_accounts)

    # Print summary
    for account in all_accounts:
        if account["value"] > 0 and account.get("source_file", "").endswith(".csv"):
             # Only print details for CSV ones here, as PDFs were printed during loop
             print(f"    - {account['name']} ({account['type']}): ₹{account['value']:,.2f}")

    # Aggregate by type
    by_type = {}
    for account in all_accounts:
        ptype = account["type"]
        if ptype not in by_type:
            by_type[ptype] = {"value": 0.0, "count": 0}
        by_type[ptype]["value"] += account["value"]
        by_type[ptype]["count"] += 1

    return {
        "generated_at": datetime.now().isoformat(),
        "accounts": all_accounts,
        "total_value": total_value,
        "account_count": len(all_accounts),
        "by_type": by_type,
        "source_file": "Multiple"
    }



def save_pension_json(data: dict) -> Path:
    """Save pension data to JSON file."""
    return save_json(data, OUTPUT_PATH / "pension_data.json", "Pension")
