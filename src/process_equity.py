"""
Complete equity processing script
Can be run standalone or imported into notebook
"""

from pathlib import Path
import json
from datetime import datetime
from equity_parsers import parse_cdsl_statement, parse_nsdl_statement, consolidate_equity_data
from upstox_api import create_upstox_client
import os


def process_all_equity_statements(equity_path: Path, sync_prices: bool = False):
    """
    Process all equity statements from CDSL and NSDL

    Args:
        equity_path: Path to equity data directory
        sync_prices: Whether to sync prices from Upstox API

    Returns:
        Consolidated equity data dictionary
    """
    all_accounts = []

    print("\n" + "=" * 60)
    print("📈 PROCESSING ALL EQUITY STATEMENTS")
    print("=" * 60 + "\n")

    # Process CDSL statements
    print("📊 Processing CDSL statements...")
    cdsl_path = equity_path / "cdsl"
    if cdsl_path.exists():
        for file_path in cdsl_path.glob("*.csv"):
            result = parse_cdsl_statement(file_path)
            if result:
                all_accounts.append(result)
                print(
                    f"  ✓ {file_path.name}: ₹{result['total_value']:,.2f} ({result['total_holdings']} holdings)"
                )
    else:
        print(f"  ⚠️  CDSL path not found: {cdsl_path}")

    # Process NSDL statements
    print("\n📊 Processing NSDL statements...")
    nsdl_path = equity_path / "nsdl"
    if nsdl_path.exists():
        # Check for subdirectories (like abhipra)
        nsdl_files = list(nsdl_path.glob("*.xlsx")) + list(nsdl_path.glob("*.xls"))

        # Also check subdirectories
        for subdir in nsdl_path.iterdir():
            if subdir.is_dir():
                nsdl_files.extend(subdir.glob("*.xlsx"))
                nsdl_files.extend(subdir.glob("*.xls"))

        for file_path in nsdl_files:
            result = parse_nsdl_statement(file_path)
            if result:
                all_accounts.append(result)
                print(
                    f"  ✓ {file_path.name}: ₹{result['total_value']:,.2f} ({result['total_holdings']} holdings)"
                )
    else:
        print(f"  ⚠️  NSDL path not found: {nsdl_path}")

    print("\n" + "=" * 60)
    print(f"✅ Total demat accounts processed: {len(all_accounts)}")
    print("=" * 60)

    # Sync prices with Upstox API if requested
    if sync_prices and len(all_accounts) > 0:
        print("\n🔄 Syncing prices with Upstox API...")
        upstox_client = create_upstox_client()

        if upstox_client:
            for account in all_accounts:
                print(f"\n📱 Updating {account['depository']}-{account['client_id']}...")
                account["holdings"] = upstox_client.update_holdings_with_ltp(account["holdings"])

                # Recalculate total value
                account["total_value"] = sum(h["value"] for h in account["holdings"])
                print(f"  ✅ Total value: ₹{account['total_value']:,.2f}")
        else:
            print("  ⚠️  Skipping price sync (Upstox API not configured)")
            print("  💡 Set UPSTOX_ACCESS_TOKEN environment variable to enable")

    # Consolidate all equity data
    consolidated = consolidate_equity_data(all_accounts)

    print("\n" + "=" * 70)
    print("📊 EQUITY PORTFOLIO SUMMARY")
    print("=" * 70)
    print(f"Total Accounts: {consolidated['total_accounts']}")
    print(f"Total Holdings: {consolidated['total_holdings']}")
    print(f"Total Value: ₹{consolidated['total_value']:,.2f}")
    print(f"  CDSL: ₹{consolidated['depositories'].get('CDSL', 0):,.2f}")
    print(f"  NSDL: ₹{consolidated['depositories'].get('NSDL', 0):,.2f}")
    print("=" * 70)

    return consolidated


def save_equity_json(equity_data: dict, output_path: Path):
    """Save equity data to JSON file"""
    json_file = output_path / "equity_data.json"

    output_data = {
        "generated_at": datetime.now().isoformat(),
        "total_value": equity_data["total_value"],
        "total_holdings": equity_data["total_holdings"],
        "total_accounts": equity_data["total_accounts"],
        "depositories": equity_data["depositories"],
        "accounts": equity_data["accounts"],
        "consolidated_holdings": equity_data["consolidated_holdings"],
    }

    with open(json_file, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\n✅ Equity JSON file created: {json_file}")
    return json_file


def combine_bank_and_equity_data(bank_data: dict, equity_data: dict, output_path: Path):
    """
    Combine bank and equity data into a single networth JSON

    Args:
        bank_data: Dictionary with bank account data
        equity_data: Dictionary with equity holdings data
        output_path: Path to output directory
    """
    networth_data = {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_networth": bank_data.get("total_balance", 0) + equity_data.get("total_value", 0),
            "bank_balance": bank_data.get("total_balance", 0),
            "equity_value": equity_data.get("total_value", 0),
        },
        "banks": bank_data,
        "equity": equity_data,
    }

    json_file = output_path / "networth_data.json"
    with open(json_file, "w") as f:
        json.dump(networth_data, f, indent=2)

    print(f"\n✅ Combined networth JSON created: {json_file}")
    print(f"\n💰 TOTAL NET WORTH: ₹{networth_data['summary']['total_networth']:,.2f}")
    print(f"   Bank Balance: ₹{networth_data['summary']['bank_balance']:,.2f}")
    print(f"   Equity Value: ₹{networth_data['summary']['equity_value']:,.2f}")

    return json_file


if __name__ == "__main__":
    # Can be run standalone
    BASE_PATH = Path(__file__).parent.parent
    DATA_PATH = BASE_PATH / "data" / "10.25"
    EQUITY_PATH = DATA_PATH / "equity"
    OUTPUT_PATH = BASE_PATH / "output"

    # Process equity
    equity_data = process_all_equity_statements(
        equity_path=EQUITY_PATH, sync_prices=False  # Set to True to sync with Upstox
    )

    # Save equity data
    save_equity_json(equity_data, OUTPUT_PATH)
