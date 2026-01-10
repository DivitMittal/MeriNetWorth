"""
Complete mutual fund processing script
Can be run standalone or imported into notebook
"""

from pathlib import Path
import json
from datetime import datetime
from mf_parsers import parse_mf_statement, consolidate_mf_data


def process_all_mf_statements(mf_path: Path):
    """
    Process all mutual fund statements

    Args:
        mf_path: Path to MF data directory

    Returns:
        Consolidated MF data dictionary
    """
    all_accounts = []

    print("\n" + "=" * 60)
    print("📊 PROCESSING ALL MUTUAL FUND STATEMENTS")
    print("=" * 60 + "\n")

    if not mf_path.exists():
        print(f"  ⚠️  MF path not found: {mf_path}")
        return consolidate_mf_data([])

    # Process all PDF files
    pdf_files = list(mf_path.glob("*.pdf"))

    if not pdf_files:
        print(f"  ⚠️  No PDF files found in {mf_path}")
        return consolidate_mf_data([])

    for file_path in pdf_files:
        result = parse_mf_statement(file_path)
        if result:
            all_accounts.append(result)
            print(
                f"  ✓ {file_path.name}: {result['holder_name']}"
            )
            print(
                f"     SoA: ₹{result['soa_value']:,.2f} ({len(result['soa_holdings'])} holdings)"
            )
            print(
                f"     Demat: ₹{result['demat_value']:,.2f} ({len(result['demat_holdings'])} holdings)"
            )
            print(
                f"     Total: ₹{result['total_value']:,.2f}"
            )

    print("\n" + "=" * 60)
    print(f"✅ Total MF accounts processed: {len(all_accounts)}")
    print("=" * 60)

    # Consolidate all MF data
    consolidated = consolidate_mf_data(all_accounts)

    print("\n" + "=" * 70)
    print("📊 MUTUAL FUND PORTFOLIO SUMMARY")
    print("=" * 70)
    print(f"Total Accounts: {consolidated['total_accounts']}")
    print(f"Total Holdings: {consolidated['total_holdings']}")
    print(f"Total Value: ₹{consolidated['total_value']:,.2f}")
    print(f"  SoA (Non-Demat): ₹{consolidated['soa_value']:,.2f}")
    print(f"  Demat: ₹{consolidated['demat_value']:,.2f}")
    print("=" * 70)

    return consolidated


def save_mf_json(mf_data: dict, output_path: Path):
    """Save mutual fund data to JSON file"""
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

    print(f"\n✅ MF JSON file created: {json_file}")
    return json_file


if __name__ == "__main__":
    # Can be run standalone
    BASE_PATH = Path(__file__).parent.parent
    DATA_PATH = BASE_PATH / "data" / "10.25"
    MF_PATH = DATA_PATH / "mf"
    OUTPUT_PATH = BASE_PATH / "output"

    # Process MF
    mf_data = process_all_mf_statements(mf_path=MF_PATH)

    # Save MF data
    save_mf_json(mf_data, OUTPUT_PATH)
