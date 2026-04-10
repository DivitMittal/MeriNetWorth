#!/usr/bin/env python3
"""
MeriNetWorth - Complete Data Processor
Process all assets: Bank, Equity, MF, Pension, Fixed Income, Real Estate, Other Assets, Liabilities
"""

import json
import sys
from datetime import datetime

from src.asset_aggregator import aggregate_by_pan, format_pan_summary
from src.asset_parsers import (
    process_other_assets,
    process_real_estate,
    save_other_assets_json,
    save_real_estate_json,
)
from src.config import (
    DATA_PATH,
    EQUITY_PATH,
    GOALS_FILE_PATH,
    HISTORY_FILE,
    MF_PATH,
    OUTPUT_PATH,
    PLANNING_CONFIG_PATH,
    PLANNING_FILE,
)
from src.fixed_income_parser import process_fixed_income, save_fixed_income_json
from src.liability_parser import process_all_liabilities, save_liabilities_json
from src.pension_parser import process_pension, save_pension_json
from src.planning_analytics import (
    build_history_snapshot,
    build_planning_data,
    upsert_history_snapshot,
)
from src.process_banks import main as process_banks_main
from src.process_equity import process_all_equity_statements, save_equity_json
from src.process_mf import process_all_mf_statements, save_mf_json


def build_legacy_networth_data(
    bank_data,
    equity_data,
    mf_data,
    pension_data,
    fixed_income_data,
    real_estate_data,
    other_assets_data,
    liabilities_data,
):
    total_networth = 0
    total_networth += bank_data.get("total_balance", 0)
    if equity_data:
        total_networth += equity_data.get("total_value", 0)
    if mf_data:
        total_networth += mf_data.get("total_value", 0)
    total_networth += pension_data.get("total_value", 0)
    total_networth += fixed_income_data.get("total_principal", 0)
    total_networth += real_estate_data.get("total_value", 0)
    total_networth += other_assets_data.get("total_value", 0)
    total_networth -= liabilities_data.get("total_liability", 0)

    return {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_networth": total_networth,
            "bank_balance": bank_data.get("total_balance", 0),
            "equity_value": equity_data.get("total_value", 0) if equity_data else 0,
            "mf_value": mf_data.get("total_value", 0) if mf_data else 0,
            "pension_value": pension_data.get("total_value", 0),
            "fixed_income_value": fixed_income_data.get("total_principal", 0),
            "real_estate_value": real_estate_data.get("total_value", 0),
            "other_assets_value": other_assets_data.get("total_value", 0),
            "liabilities": liabilities_data.get("total_liability", 0),
        },
        "banks": bank_data,
        "equity": equity_data,
        "mf": mf_data,
        "pension": pension_data,
        "fixed_income": fixed_income_data,
        "real_estate": real_estate_data,
        "other_assets": other_assets_data,
        "liabilities": liabilities_data,
    }


def load_planning_targets(config_path):
    if not config_path.exists():
        return None
    with open(config_path) as f:
        config = json.load(f)
    return config.get("target_allocation")


def main():
    """Process all data sources."""
    print("\n" + "=" * 70)
    print("🏦 MeriNetWorth - Complete Data Processor")
    print("=" * 70 + "\n")

    # Step 1: Bank Accounts
    print("STEP 1: Processing Bank Accounts")
    print("-" * 70)
    bank_result = process_banks_main()
    if bank_result != 0:
        print("❌ Bank processing failed. Proceeding with caution...")

    # Load bank data for aggregation
    bank_data = {}
    bank_json = OUTPUT_PATH / "bank_data.json"
    if bank_json.exists():
        with open(bank_json) as f:
            bank_data = json.load(f)

    # Step 2: Equity Holdings
    print("\n\nSTEP 2: Processing Equity Holdings")
    print("-" * 70)
    equity_data = None
    if not EQUITY_PATH.exists():
        print(f"⚠️  Equity path not found: {EQUITY_PATH}")
    else:
        try:
            equity_data = process_all_equity_statements(equity_path=EQUITY_PATH, sync_prices=False)
            save_equity_json(equity_data, OUTPUT_PATH)
        except Exception as e:
            print(f"⚠️  Error processing equity: {str(e)}")

    # Step 3: Mutual Funds
    print("\n\nSTEP 3: Processing Mutual Funds")
    print("-" * 70)
    try:
        mf_data = process_all_mf_statements(mf_path=MF_PATH)
        save_mf_json(mf_data, OUTPUT_PATH)
    except Exception as e:
        print(f"⚠️  Error processing mutual funds: {str(e)}")
        mf_data = None

    # Step 4: Pension (NPS/EPF)
    print("\n\nSTEP 4: Processing Pension Assets")
    print("-" * 70)
    pension_data = process_pension()
    save_pension_json(pension_data)

    # Step 5: Fixed Income (FDs)
    print("\n\nSTEP 5: Processing Fixed Income")
    print("-" * 70)
    fixed_income_data = process_fixed_income()
    save_fixed_income_json(fixed_income_data)

    # Step 6: Real Estate
    print("\n\nSTEP 6: Processing Real Estate")
    print("-" * 70)
    real_estate_data = process_real_estate()
    save_real_estate_json(real_estate_data)

    # Step 7: Other Assets
    print("\n\nSTEP 7: Processing Other Assets")
    print("-" * 70)
    other_assets_data = process_other_assets()
    save_other_assets_json(other_assets_data)

    # Step 8: Liabilities
    print("\n\nSTEP 8: Processing Liabilities")
    print("-" * 70)
    liabilities_data = process_all_liabilities()
    save_liabilities_json(liabilities_data)

    # Step 9: Aggregation & Net Worth
    print("\n\nSTEP 9: Aggregating Net Worth")
    print("-" * 70)

    aggregated_assets = aggregate_by_pan(
        bank_data=bank_data,
        equity_data=equity_data,
        mf_data=mf_data,
        pension_data=pension_data,
        fixed_income_data=fixed_income_data,
        real_estate_data=real_estate_data,
        other_assets_data=other_assets_data,
        liabilities_data=liabilities_data,
    )

    # Print Summary
    print(format_pan_summary(aggregated_assets))

    legacy_networth_data = build_legacy_networth_data(
        bank_data=bank_data,
        equity_data=equity_data,
        mf_data=mf_data,
        pension_data=pension_data,
        fixed_income_data=fixed_income_data,
        real_estate_data=real_estate_data,
        other_assets_data=other_assets_data,
        liabilities_data=liabilities_data,
    )
    total_networth = legacy_networth_data["summary"]["total_networth"]

    with open(OUTPUT_PATH / "networth_data.json", "w") as f:
        json.dump(legacy_networth_data, f, indent=2)
    print(f"JSON file created: {OUTPUT_PATH / 'networth_data.json'}")

    planning_data = build_planning_data(
        networth_data=legacy_networth_data,
        fixed_income_data=fixed_income_data,
        mf_data=mf_data,
        equity_data=equity_data,
        goals_path=GOALS_FILE_PATH,
        targets=load_planning_targets(PLANNING_CONFIG_PATH),
    )
    with open(PLANNING_FILE, "w") as f:
        json.dump(planning_data, f, indent=2)
    print(f"JSON file created: {PLANNING_FILE}")

    snapshot = build_history_snapshot(DATA_PATH.name, legacy_networth_data)
    upsert_history_snapshot(HISTORY_FILE, snapshot)
    print(f"JSON file created: {HISTORY_FILE}")

    print("\n\n" + "=" * 70)
    print("✅ PROCESSING COMPLETE")
    print("=" * 70)
    print(f"Total Net Worth: ₹{total_networth:,.2f}")

    print("\n📊 Generated Files:")
    print("   • output/bank_data.json")
    print("   • output/equity_data.json")
    print("   • output/mf_data.json")
    print("   • output/pension_data.json")
    print("   • output/fixed_income_data.json")
    print("   • output/real_estate_data.json")
    print("   • output/other_assets_data.json")
    print("   • output/liabilities_data.json")
    print("   • output/networth_data.json")
    print("   • output/planning_data.json")
    print("   • output/history_data.json")

    return 0


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
