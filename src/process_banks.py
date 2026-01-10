#!/usr/bin/env python3
"""
Bank Account Data Processor
Extract and consolidate bank account balances from various bank statements
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import warnings
import sys

warnings.filterwarnings('ignore')

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))


# Configuration
BASE_PATH = Path(__file__).parent.parent
DATA_PATH = BASE_PATH / 'data' / '10.25'
BANK_PATH = DATA_PATH / 'bank'
OUTPUT_PATH = BASE_PATH / 'output'

# Create output directory if it doesn't exist
OUTPUT_PATH.mkdir(exist_ok=True)


def clean_amount(value):
    """Convert various amount formats to float"""
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    # Remove currency symbols, commas, and convert to float
    cleaned = str(value).replace('₹', '').replace(',', '').replace('INR', '').strip()
    try:
        return float(cleaned)
    except:
        return 0.0


def extract_account_number(text):
    """Extract account number from text, handling masked numbers"""
    if pd.isna(text):
        return ''
    return str(text).strip()


def standardize_holder_name(name):
    """Standardize holder names for consistency"""
    if pd.isna(name):
        return ''
    name = str(name).strip()
    # Common standardizations
    replacements = {
        'Mrs.': '',
        'Mr.': '',
        'Ms.': '',
        'MITAL': 'Mittal',
        'MITTAL': 'Mittal'
    }
    for old, new in replacements.items():
        name = name.replace(old, new)
    return name.strip()


def parse_idfc_statement(file_path):
    """Parse IDFC First Bank Excel statement"""
    try:
        df = pd.read_excel(file_path, sheet_name='Account Statement')

        # Extract account details from header rows
        account_number = ''
        holder_name = ''
        closing_balance = 0.0

        # Find account number (usually in row with 'ACCOUNT NUMBER')
        for idx, row in df.iterrows():
            if 'ACCOUNT NUMBER' in str(row[0]):
                account_number = extract_account_number(row[1])
            elif 'CUSTOMER NAME' in str(row[0]):
                holder_name = standardize_holder_name(row[1])
            elif 'Closing Balance' in str(row[0]):
                closing_balance = clean_amount(row[3])
                break

        return {
            'bank': 'IDFC FIRST',
            'account_number': account_number,
            'holder_name': holder_name,
            'balance': closing_balance,
            'source_file': file_path.name
        }
    except Exception as e:
        print(f"❌ Error parsing IDFC file {file_path.name}: {str(e)}")
        return None


def parse_equitas_statement(file_path):
    """Parse Equitas Small Finance Bank Excel statement"""
    try:
        df = pd.read_excel(file_path, sheet_name=0)

        account_number = ''
        holder_name = ''
        closing_balance = 0.0

        # Equitas has a specific structure
        for idx, row in df.iterrows():
            if 'Account Number' in str(row[1]):
                account_number = extract_account_number(row[7])
            elif 'Customer Name' in str(row[1]):
                holder_name = standardize_holder_name(row[2])
            elif 'Available Balance' in str(row[4]):
                closing_balance = clean_amount(row[5])

        # If closing balance not found in header, get from last transaction
        if closing_balance == 0.0:
            for idx in range(len(df) - 1, -1, -1):
                if 'End of the Statement' not in str(df.iloc[idx, 0]):
                    last_balance = clean_amount(df.iloc[idx, -1])
                    if last_balance > 0:
                        closing_balance = last_balance
                        break

        return {
            'bank': 'Equitas',
            'account_number': account_number,
            'holder_name': holder_name,
            'balance': closing_balance,
            'source_file': file_path.name
        }
    except Exception as e:
        print(f"❌ Error parsing Equitas file {file_path.name}: {str(e)}")
        return None


def parse_bandhan_statement(file_path):
    """Parse Bandhan Bank CSV statement"""
    try:
        # Read entire file as text to parse header information
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()

        account_number = ''
        holder_name = ''
        closing_balance = 0.0

        # Parse header information
        for i, line in enumerate(lines):
            if 'Full Name of Customer' in line:
                holder_name = line.split(',', 1)[1].strip() if ',' in line else ''
                holder_name = standardize_holder_name(holder_name)
            elif 'Account Number' in line:
                account_number = line.split(',', 1)[1].strip() if ',' in line else file_path.stem
            elif line.startswith('Opening Balance'):
                # Statement Summary line format: Opening Balance,Debits,Credits,Closing Balance
                # Next line has values: INR2238.38,INR0.00,INR33.00,INR2271.38
                if i + 1 < len(lines):
                    summary_line = lines[i + 1].strip()
                    parts = summary_line.split(',')
                    if len(parts) >= 4:
                        # Closing balance is the 4th column
                        closing_balance = clean_amount(parts[3])
                    break

        return {
            'bank': 'Bandhan',
            'account_number': account_number,
            'holder_name': holder_name,
            'balance': closing_balance,
            'source_file': file_path.name
        }
    except Exception as e:
        print(f"❌ Error parsing Bandhan file {file_path.name}: {str(e)}")
        return None


def parse_icici_statement(file_path):
    """Parse ICICI Bank XLS statement"""
    try:
        df = pd.read_excel(file_path)

        closing_balance = 0.0

        # Try to find balance column
        balance_cols = [col for col in df.columns if 'balance' in str(col).lower()]
        if balance_cols:
            closing_balance = clean_amount(df[balance_cols[0]].dropna().iloc[-1])

        return {
            'bank': 'ICICI',
            'account_number': file_path.stem,
            'holder_name': '',
            'balance': closing_balance,
            'source_file': file_path.name
        }
    except Exception as e:
        print(f"❌ Error parsing ICICI file {file_path.name}: {str(e)}")
        return None


def parse_indusind_statement(file_path):
    """Parse IndusInd Bank CSV statement"""
    try:
        df = pd.read_csv(file_path)

        closing_balance = 0.0
        balance_cols = [col for col in df.columns if 'balance' in col.lower()]

        if balance_cols:
            closing_balance = clean_amount(df[balance_cols[0]].iloc[-1])

        return {
            'bank': 'IndusInd',
            'account_number': file_path.stem,
            'holder_name': '',
            'balance': closing_balance,
            'source_file': file_path.name
        }
    except Exception as e:
        print(f"❌ Error parsing IndusInd file {file_path.name}: {str(e)}")
        return None


def process_all_bank_statements():
    """Process all bank statements and consolidate data"""
    all_accounts = []

    print("\n" + "="*60)
    print("🏦 PROCESSING ALL BANK STATEMENTS")
    print("="*60 + "\n")

    # IDFC First Bank
    print("📊 Processing IDFC First Bank...")
    idfc_path = BANK_PATH / 'IDFCFirst'
    if idfc_path.exists():
        for file_path in idfc_path.glob('*.xlsx'):
            result = parse_idfc_statement(file_path)
            if result:
                all_accounts.append(result)
                print(f"  ✓ {file_path.name}: ₹{result['balance']:,.2f}")

    # Equitas Bank
    print("\n📊 Processing Equitas Bank...")
    equitas_path = BANK_PATH / 'Equitas'
    if equitas_path.exists():
        for file_path in equitas_path.glob('*.xlsx'):
            result = parse_equitas_statement(file_path)
            if result:
                all_accounts.append(result)
                print(f"  ✓ {file_path.name}: ₹{result['balance']:,.2f}")

    # Bandhan Bank
    print("\n📊 Processing Bandhan Bank...")
    bandhan_path = BANK_PATH / 'Bandhan'
    if bandhan_path.exists():
        for file_path in bandhan_path.glob('*.csv'):
            result = parse_bandhan_statement(file_path)
            if result:
                all_accounts.append(result)
                print(f"  ✓ {file_path.name}: ₹{result['balance']:,.2f}")

    # ICICI Bank
    print("\n📊 Processing ICICI Bank...")
    icici_path = BANK_PATH / 'ICICI'
    if icici_path.exists():
        for file_path in icici_path.glob('*.xls'):
            result = parse_icici_statement(file_path)
            if result:
                all_accounts.append(result)
                print(f"  ✓ {file_path.name}: ₹{result['balance']:,.2f}")

    # IndusInd Bank
    print("\n📊 Processing IndusInd Bank...")
    indusind_path = BANK_PATH / 'IndusInd'
    if indusind_path.exists():
        for file_path in indusind_path.glob('*.csv'):
            result = parse_indusind_statement(file_path)
            if result:
                all_accounts.append(result)
                print(f"  ✓ {file_path.name}: ₹{result['balance']:,.2f}")

    print("\n" + "="*60)
    print(f"✅ Total accounts processed: {len(all_accounts)}")
    print("="*60)

    return pd.DataFrame(all_accounts)


def export_to_excel(accounts_df):
    """Export consolidated data to Excel in FFS format"""

    # Generate filename with current date
    today = datetime.now().strftime('%b\'%y')
    output_file = OUTPUT_PATH / f'Bank-Consolidated-{today}.xlsx'

    # Create Excel writer
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Sheet 1: Raw Data
        accounts_df.to_excel(writer, sheet_name='Raw Data', index=False)

        # Sheet 2: Summary by Bank
        summary = accounts_df.groupby('bank').agg({
            'balance': 'sum',
            'account_number': 'count'
        }).rename(columns={'account_number': 'num_accounts'})
        summary.to_excel(writer, sheet_name='Summary')

        # Sheet 3: FFS Format
        ffs_data = []
        for _, row in accounts_df.iterrows():
            ffs_data.append({
                'A/c.': f"{row['bank']} - {row['holder_name']}".strip(),
                'A/c. No.': row['account_number'],
                'Balance': row['balance']
            })

        ffs_df = pd.DataFrame(ffs_data)
        ffs_df.to_excel(writer, sheet_name=f'Bank - {today}', index=False)

    print(f"\n✅ Excel file created: {output_file}")
    return output_file


def save_json_for_dashboard(accounts_df):
    """Save JSON for web visualization"""
    # Prepare data for web visualization
    web_data = {
        'generated_at': datetime.now().isoformat(),
        'total_balance': float(accounts_df['balance'].sum()),
        'total_accounts': len(accounts_df),
        'banks': accounts_df.groupby('bank')['balance'].sum().to_dict(),
        'accounts': accounts_df.to_dict('records')
    }

    # Save to JSON
    json_file = OUTPUT_PATH / 'bank_data.json'
    with open(json_file, 'w') as f:
        json.dump(web_data, f, indent=2)

    print(f"✅ JSON file created: {json_file}")
    return json_file


def main():
    """Main processing function"""
    try:
        print("\n" + "="*70)
        print("MeriNetWorth - Bank Data Processor")
        print("="*70)
        print(f"\n📂 Data Path: {DATA_PATH}")
        print(f"📂 Bank Path: {BANK_PATH}")
        print(f"📂 Output Path: {OUTPUT_PATH}")

        # Check if bank path exists
        if not BANK_PATH.exists():
            print(f"\n❌ Error: Bank path does not exist: {BANK_PATH}")
            print("   Please ensure bank statements are in the correct directory.")
            return 1

        # Process all statements
        accounts_df = process_all_bank_statements()

        if len(accounts_df) == 0:
            print("\n⚠️  Warning: No accounts processed. Check your data directory.")
            return 1

        # Display summary
        total_balance = accounts_df['balance'].sum()
        print(f"\n💰 SUMMARY")
        print("="*60)
        print(f"Total Balance: ₹{total_balance:,.2f}")
        print(f"Total Balance: ₹{total_balance/100000:.2f} Lakhs")
        if total_balance >= 10000000:
            print(f"Total Balance: ₹{total_balance/10000000:.2f} Crores")

        # Export to Excel
        export_to_excel(accounts_df)

        # Save JSON for dashboard
        save_json_for_dashboard(accounts_df)

        print("\n" + "="*70)
        print("✅ Processing complete!")
        print("="*70)
        print("\n📊 Next steps:")
        print("   1. Review: output/Bank-Consolidated-*.xlsx")
        print("   2. Launch dashboard: streamlit run web/app.py")

        return 0

    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
