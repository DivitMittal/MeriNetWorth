#!/usr/bin/env python3
"""Inspect all NSDL Excel files to understand structure"""

import pandas as pd
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent.parent
nsdl_path = PROJECT_ROOT / "data" / "10.25" / "equity" / "nsdl"

print("=" * 80)
print("Inspecting NSDL Excel Files")
print("=" * 80)

# Find all NSDL files
nsdl_files = list(nsdl_path.glob("*.xlsx")) + list(nsdl_path.glob("*.xls"))

# Also check subdirectories
for subdir in nsdl_path.iterdir():
    if subdir.is_dir():
        nsdl_files.extend(subdir.glob("*.xlsx"))
        nsdl_files.extend(subdir.glob("*.xls"))

print(f"\nFound {len(nsdl_files)} NSDL files\n")

for file_path in nsdl_files[:3]:  # Check first 3 files
    print("\n" + "=" * 80)
    print(f"File: {file_path.name}")
    print("=" * 80)

    try:
        # Read the Excel file
        df = pd.read_excel(file_path, sheet_name=0)

        print(f"Shape: {df.shape} (rows x columns)")
        print(f"\nColumns ({len(df.columns)}):")
        for i, col in enumerate(df.columns):
            print(f"  {i}: {col}")

        print(f"\nFirst 5 non-empty rows:")
        # Filter out completely empty rows
        non_empty = df.dropna(how="all").head(5)
        for idx in non_empty.index:
            row = df.iloc[idx]
            print(f"\nRow {idx}:")
            for col in df.columns:
                if pd.notna(row[col]):
                    print(f"  {col}: {row[col]}")

        # Look for patterns
        print("\n" + "-" * 80)
        print("Column Analysis:")
        for col in df.columns:
            col_str = str(col).lower()
            if any(keyword in col_str for keyword in ["isin", "security", "name", "symbol"]):
                print(f"  ✓ Name column candidate: '{col}'")
            if any(
                keyword in col_str for keyword in ["quantity", "balance", "holding", "unit", "qty"]
            ):
                print(f"  ✓ Quantity column candidate: '{col}'")

    except Exception as e:
        print(f"  ❌ Error reading file: {str(e)}")
        import traceback

        traceback.print_exc()

print("\n" + "=" * 80)
print("Done")
print("=" * 80)
