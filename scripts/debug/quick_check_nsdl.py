#!/usr/bin/env python3
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent

file1 = PROJECT_ROOT / "data" / "10.25" / "equity" / "nsdl" / "5150828IN30302884293108.xlsx"
print(f"Checking: {file1.name}")
print("=" * 60)

try:
    df = pd.read_excel(file1, sheet_name=0)
    print(f"Columns: {list(df.columns)}")
    print(f"\nFirst few rows:")
    print(df.head(10))
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)

file2 = (
    PROJECT_ROOT / "data" / "10.25" / "equity" / "nsdl" / "abhipra" / "5150800IN30020610786845.xlsx"
)
print(f"\nChecking: {file2.name}")
print("=" * 60)

try:
    df = pd.read_excel(file2, sheet_name=0)
    print(f"Columns: {list(df.columns)}")
    print(f"\nFirst few rows:")
    print(df.head(10))
except Exception as e:
    print(f"Error: {e}")
