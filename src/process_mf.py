from pathlib import Path
import json
from datetime import datetime
from mf_parsers import parse_mf_statement, consolidate_mf_data
from src.config import BASE_PATH, DATA_PATH, MF_PATH, OUTPUT_PATH


def process_all_mf_statements(mf_path: Path):
    all_accounts = []

    print("\nProcessing mutual fund statements\n")

    if not mf_path.exists():
        print(f"  MF path not found: {mf_path}")
        return consolidate_mf_data([])

    pdf_files = list(mf_path.glob("*.pdf"))

    if not pdf_files:
        print(f"  No PDF files found in {mf_path}")
        return consolidate_mf_data([])

    for file_path in pdf_files:
        result = parse_mf_statement(file_path)
        if result:
            all_accounts.append(result)
            print(f"  {file_path.name}: {result['holder_name']}")
            print(f"     SoA: {result['soa_value']:,.2f} ({len(result['soa_holdings'])} holdings)")
            print(f"     Demat: {result['demat_value']:,.2f} ({len(result['demat_holdings'])} holdings)")
            print(f"     Total: {result['total_value']:,.2f}")

    print(f"\nTotal MF accounts processed: {len(all_accounts)}\n")

    consolidated = consolidate_mf_data(all_accounts)

    print("\nMUTUAL FUND PORTFOLIO SUMMARY")
    print(f"Total Accounts: {consolidated['total_accounts']}")
    print(f"Total Holdings: {consolidated['total_holdings']}")
    print(f"Total Value: {consolidated['total_value']:,.2f}")
    print(f"  SoA (Non-Demat): {consolidated['soa_value']:,.2f}")
    print(f"  Demat: {consolidated['demat_value']:,.2f}")

    return consolidated


def save_mf_json(mf_data: dict, output_path: Path):
    json_file = output_path / "mf_data.json"

    output_data = {
        "generated_at": datetime.now().isoformat(),
        "total_value": mf_data["total_value"],
        "total_holdings": mf_data["total_holdings"],
        "total_accounts": mf_data["total_accounts"],
        "soa_value": mf_data["soa_value"],
        "demat_value": mf_data["demat_value"],
        "accounts": mf_data["accounts"],
        "consolidated_holdings": mf_data["consolidated_holdings"],
    }

    with open(json_file, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\nMF JSON file created: {json_file}")
    return json_file


if __name__ == "__main__":
    mf_data = process_all_mf_statements(mf_path=MF_PATH)
    save_mf_json(mf_data, OUTPUT_PATH)
