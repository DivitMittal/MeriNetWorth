#!/usr/bin/env python3
"""
MeriNetWorth - Complete Data Processor
Process both bank accounts and equity holdings in one run
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from process_banks import main as process_banks_main
from process_equity import (
    process_all_equity_statements,
    save_equity_json,
    combine_bank_and_equity_data
)
import json


def main():
    """Process all data: banks + equity"""
    print("\n" + "="*70)
    print("🏦 MeriNetWorth - Complete Data Processor")
    print("="*70 + "\n")

    # Step 1: Process bank accounts
    print("STEP 1: Processing Bank Accounts")
    print("-" * 70)
    bank_result = process_banks_main()

    if bank_result != 0:
        print("\n❌ Bank processing failed. Stopping.")
        return 1

    # Step 2: Process equity holdings
    print("\n\nSTEP 2: Processing Equity Holdings")
    print("-" * 70)

    base_path = Path(__file__).parent
    equity_path = base_path / 'data' / '10.25' / 'equity'
    output_path = base_path / 'output'

    if not equity_path.exists():
        print(f"⚠️  Equity path not found: {equity_path}")
        print("   Skipping equity processing.")
        equity_data = None
    else:
        try:
            # Process equity (without Upstox sync by default)
            equity_data = process_all_equity_statements(
                equity_path=equity_path,
                sync_prices=False  # Set to True to sync with Upstox
            )

            # Save equity data
            save_equity_json(equity_data, output_path)

            # Combine with bank data
            bank_json = output_path / 'bank_data.json'
            if bank_json.exists():
                with open(bank_json, 'r') as f:
                    bank_data = json.load(f)
                combine_bank_and_equity_data(bank_data, equity_data, output_path)

        except Exception as e:
            print(f"\n⚠️  Error processing equity: {str(e)}")
            print("   Continuing with bank data only.")
            equity_data = None

    # Final summary
    print("\n\n" + "="*70)
    print("✅ PROCESSING COMPLETE")
    print("="*70)

    print("\n📊 Generated Files:")
    print(f"   • output/bank_data.json")
    print(f"   • output/Bank-Consolidated-*.xlsx")

    if equity_data:
        print(f"   • output/equity_data.json")
        print(f"   • output/networth_data.json")

    print("\n🚀 Next Steps:")
    print("   1. Review generated files in output/")
    print("   2. Launch dashboard: streamlit run web/app.py")
    print("   3. Or use quick launcher: ./run_dashboard.sh")

    print("\n💡 Tip: To sync equity prices with Upstox API:")
    print("   export UPSTOX_ACCESS_TOKEN='your_token'")
    print("   python process_all.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
