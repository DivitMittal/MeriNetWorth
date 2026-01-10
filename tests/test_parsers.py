#!/usr/bin/env python3
"""
Test individual bank parsers
"""

import sys
from pathlib import Path

# Project root is parent of tests/
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT / "src"))

from process_banks import (
    parse_bandhan_statement,
    parse_idfc_statement,
    parse_equitas_statement,
    parse_icici_statement,
    parse_indusind_statement,
)


def test_bandhan():
    """Test Bandhan parser"""
    print("\n" + "=" * 60)
    print("Testing Bandhan Parser")
    print("=" * 60)

    bank_path = PROJECT_ROOT / "data" / "10.25" / "bank" / "Bandhan"
    if not bank_path.exists():
        print(f"❌ Path does not exist: {bank_path}")
        return

    for csv_file in bank_path.glob("*.csv"):
        print(f"\nProcessing: {csv_file.name}")
        result = parse_bandhan_statement(csv_file)
        if result:
            print(f"  ✓ Account: {result['account_number']}")
            print(f"  ✓ Holder: {result['holder_name']}")
            print(f"  ✓ Balance: ₹{result['balance']:,.2f}")
        else:
            print(f"  ❌ Failed to parse")


def test_idfc():
    """Test IDFC parser"""
    print("\n" + "=" * 60)
    print("Testing IDFC Parser")
    print("=" * 60)

    bank_path = PROJECT_ROOT / "data" / "10.25" / "bank" / "IDFCFirst"
    if not bank_path.exists():
        print(f"⚠️  Path does not exist: {bank_path}")
        return

    for xlsx_file in bank_path.glob("*.xlsx"):
        print(f"\nProcessing: {xlsx_file.name}")
        result = parse_idfc_statement(xlsx_file)
        if result:
            print(f"  ✓ Account: {result['account_number']}")
            print(f"  ✓ Holder: {result['holder_name']}")
            print(f"  ✓ Balance: ₹{result['balance']:,.2f}")


def test_equitas():
    """Test Equitas parser"""
    print("\n" + "=" * 60)
    print("Testing Equitas Parser")
    print("=" * 60)

    bank_path = PROJECT_ROOT / "data" / "10.25" / "bank" / "Equitas"
    if not bank_path.exists():
        print(f"⚠️  Path does not exist: {bank_path}")
        return

    for xlsx_file in bank_path.glob("*.xlsx"):
        print(f"\nProcessing: {xlsx_file.name}")
        result = parse_equitas_statement(xlsx_file)
        if result:
            print(f"  ✓ Account: {result['account_number']}")
            print(f"  ✓ Holder: {result['holder_name']}")
            print(f"  ✓ Balance: ₹{result['balance']:,.2f}")


def main():
    """Run all tests"""
    try:
        test_bandhan()
        test_idfc()
        test_equitas()

        print("\n" + "=" * 60)
        print("✅ Testing complete")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
