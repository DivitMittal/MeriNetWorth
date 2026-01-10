#!/usr/bin/env python3
"""Inspect NSDL Excel file structure"""

import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
file_path = PROJECT_ROOT / "data" / "10.25" / "equity" / "nsdl" / "5150801IN30021411722076.xlsx"

print(f"Inspecting: {file_path.name}\n")

# Try to read the Excel file
excel_file = pd.ExcelFile(file_path)
print(f"Sheets: {excel_file.sheet_names}\n")

# Read the first sheet
df = pd.read_excel(file_path, sheet_name=0)

print(f"Shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}\n")

print("First 20 rows:")
print("=" * 80)
for i in range(min(20, len(df))):
    print(f"Row {i}: {df.iloc[i].to_dict()}")

print("\n" + "=" * 80)
print("\nLooking for ISIN and quantity columns...")
for col in df.columns:
    col_lower = str(col).lower()
    if "isin" in col_lower or "security" in col_lower or "name" in col_lower:
        print(f"  Found potential name column: {col}")
        print(f"    Sample values: {df[col].head(3).tolist()}")
    if (
        "quantity" in col_lower
        or "balance" in col_lower
        or "holding" in col_lower
        or "unit" in col_lower
    ):
        print(f"  Found potential quantity column: {col}")
        print(f"    Sample values: {df[col].head(3).tolist()}")
