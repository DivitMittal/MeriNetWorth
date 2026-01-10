#!/usr/bin/env python3
"""Test equity processing"""

import sys
from pathlib import Path

# Project root is parent of tests/
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT / "src"))

from process_equity import process_all_equity_statements, save_equity_json


def main():
    """Test equity processing"""
    equity_path = PROJECT_ROOT / "data" / "10.25" / "equity"
    output_path = PROJECT_ROOT / "output"

    if not equity_path.exists():
        print(f"❌ Equity path not found: {equity_path}")
        return 1

    try:
        print("\n" + "=" * 70)
        print("Testing Equity Processing")
        print("=" * 70)

        # Process equity (without Upstox sync)
        equity_data = process_all_equity_statements(equity_path=equity_path, sync_prices=False)

        if equity_data and equity_data.get("total_holdings", 0) > 0:
            print("\n✅ Equity processing successful!")
            print(f"   Total Holdings: {equity_data['total_holdings']}")
            print(f"   Total Value: ₹{equity_data['total_value']:,.2f}")
            print(f"   Total Accounts: {equity_data['total_accounts']}")

            # Save to JSON
            save_equity_json(equity_data, output_path)
        else:
            print("\n⚠️  No equity data processed")

        return 0

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
