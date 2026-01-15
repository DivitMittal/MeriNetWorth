from pathlib import Path
import json
from datetime import datetime
from equity_parsers import parse_cdsl_statement, parse_nsdl_statement, consolidate_equity_data
from upstox_api import create_upstox_client
from src.config import BASE_PATH, DATA_PATH, EQUITY_PATH, OUTPUT_PATH
import os


def process_all_equity_statements(equity_path: Path, sync_prices: bool = False):
    all_accounts = []

    print("\nProcessing equity statements\n")

    print("CDSL statements")
    cdsl_path = equity_path / "cdsl"
    if cdsl_path.exists():
        for file_path in cdsl_path.glob("*.csv"):
            result = parse_cdsl_statement(file_path)
            if result:
                all_accounts.append(result)
                print(f"  {file_path.name}: {result['total_value']:,.2f} ({result['total_holdings']} holdings)")
    else:
        print(f"  CDSL path not found: {cdsl_path}")

    print("\nNSDL statements")
    nsdl_path = equity_path / "nsdl"
    if nsdl_path.exists():
        nsdl_files = list(nsdl_path.glob("*.xlsx")) + list(nsdl_path.glob("*.xls"))

        for subdir in nsdl_path.iterdir():
            if subdir.is_dir():
                nsdl_files.extend(subdir.glob("*.xlsx"))
                nsdl_files.extend(subdir.glob("*.xls"))

        for file_path in nsdl_files:
            result = parse_nsdl_statement(file_path)
            if result:
                all_accounts.append(result)
                print(f"  {file_path.name}: {result['total_value']:,.2f} ({result['total_holdings']} holdings)")
    else:
        print(f"  NSDL path not found: {nsdl_path}")

    print(f"\nTotal demat accounts processed: {len(all_accounts)}\n")

    if sync_prices and len(all_accounts) > 0:
        print("\nSyncing prices with Upstox API...")
        upstox_client = create_upstox_client()

        if upstox_client:
            for account in all_accounts:
                print(f"\nUpdating {account['depository']}-{account['client_id']}...")
                account["holdings"] = upstox_client.update_holdings_with_ltp(account["holdings"])
                account["total_value"] = sum(h["value"] for h in account["holdings"])
                print(f"  Total value: {account['total_value']:,.2f}")
        else:
            print("  Skipping price sync (Upstox API not configured)")
            print("  Set UPSTOX_ACCESS_TOKEN environment variable to enable")

    consolidated = consolidate_equity_data(all_accounts)

    print("\nEQUITY PORTFOLIO SUMMARY")
    print(f"Total Accounts: {consolidated['total_accounts']}")
    print(f"Total Holdings: {consolidated['total_holdings']}")
    print(f"Total Value: {consolidated['total_value']:,.2f}")
    print(f"  CDSL: {consolidated['depositories'].get('CDSL', 0):,.2f}")
    print(f"  NSDL: {consolidated['depositories'].get('NSDL', 0):,.2f}")

    return consolidated


def save_equity_json(equity_data: dict, output_path: Path):
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

    print(f"\nEquity JSON file created: {json_file}")
    return json_file


def combine_bank_and_equity_data(bank_data: dict, equity_data: dict, output_path: Path):
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

    print(f"\nCombined networth JSON created: {json_file}")
    print(f"\nTOTAL NET WORTH: {networth_data['summary']['total_networth']:,.2f}")
    print(f"   Bank Balance: {networth_data['summary']['bank_balance']:,.2f}")
    print(f"   Equity Value: {networth_data['summary']['equity_value']:,.2f}")

    return json_file


if __name__ == "__main__":
    equity_data = process_all_equity_statements(
        equity_path=EQUITY_PATH, sync_prices=False
    )

    save_equity_json(equity_data, OUTPUT_PATH)
