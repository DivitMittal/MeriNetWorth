#!/usr/bin/env python3
"""Diagnostic script for NSDL files - outputs to file"""

import pandas as pd
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent.parent
output_file = PROJECT_ROOT / "nsdl_diagnosis.txt"
nsdl_path = PROJECT_ROOT / "data" / "10.25" / "equity" / "nsdl"

with open(output_file, "w") as out:
    out.write("=" * 80 + "\n")
    out.write("NSDL File Structure Diagnosis\n")
    out.write("=" * 80 + "\n\n")

    if not nsdl_path.exists():
        out.write(f"ERROR: Path does not exist: {nsdl_path}\n")
        sys.exit(1)

    # Find all NSDL files
    nsdl_files = list(nsdl_path.glob("*.xlsx")) + list(nsdl_path.glob("*.xls"))
    out.write(f"Found {len(nsdl_files)} NSDL files\n\n")

    # Check first 3 files
    for file_path in nsdl_files[:3]:
        out.write("\n" + "=" * 80 + "\n")
        out.write(f"File: {file_path.name}\n")
        out.write("=" * 80 + "\n")

        try:
            # Read the Excel file
            df = pd.read_excel(file_path, sheet_name=0)

            out.write(f"Shape: {df.shape} (rows x columns)\n")
            out.write(f"\nColumn Names ({len(df.columns)}):\n")
            for i, col in enumerate(df.columns):
                out.write(f"  [{i}] {col}\n")

            out.write(f"\nFirst 3 rows with data:\n")
            for idx in range(min(3, len(df))):
                row = df.iloc[idx]
                out.write(f"\nRow {idx}:\n")
                for col in df.columns:
                    if pd.notna(row[col]):
                        out.write(f"  {col}: {row[col]}\n")

            # Column analysis
            out.write("\n" + "-" * 80 + "\n")
            out.write("Column Keyword Analysis:\n")
            for col in df.columns:
                col_str = str(col).lower().strip()
                matches = []

                if any(keyword in col_str for keyword in ["isin", "code", "symbol"]):
                    matches.append("ISIN/CODE")
                if any(
                    keyword in col_str for keyword in ["name", "security", "scrip", "description"]
                ):
                    matches.append("NAME")
                if any(
                    keyword in col_str
                    for keyword in ["quantity", "balance", "holding", "unit", "qty", "shares"]
                ):
                    matches.append("QUANTITY")

                if matches:
                    out.write(f"  '{col}' -> {', '.join(matches)}\n")

        except Exception as e:
            out.write(f"ERROR: {str(e)}\n")
            import traceback

            out.write(traceback.format_exc())

print(f"Diagnosis written to {output_file}")
print("Run: cat nsdl_diagnosis.txt")
