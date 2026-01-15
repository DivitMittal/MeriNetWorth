import pandas as pd
import json
from datetime import datetime
import sys

from src.config import BASE_PATH, DATA_PATH, BANK_PATH, OUTPUT_PATH
from src.bank_parsers import clean_amount, extract_account_number, standardize_holder_name


def parse_idfc_statement(file_path):
    try:
        df = pd.read_excel(file_path, sheet_name='Account Statement')

        account_number = ''
        holder_name = ''
        closing_balance = 0.0

        for idx, row in df.iterrows():
            if 'ACCOUNT NUMBER' in str(row[0]):
                account_number = extract_account_number(row[1])
            elif 'CUSTOMER NAME' in str(row[0]):
                holder_name = standardize_holder_name(row[1])
            elif 'Opening Balance' in str(row[0]) and 'Closing Balance' in str(row[3]):
                if idx + 1 < len(df):
                    closing_balance = clean_amount(df.iloc[idx + 1][3])
                    break

        return {
            'bank': 'IDFC FIRST',
            'account_number': account_number,
            'holder_name': holder_name,
            'balance': closing_balance,
            'source_file': file_path.name
        }
    except Exception as e:
        print(f"Error parsing IDFC file {file_path.name}: {str(e)}")
        return None


def parse_equitas_statement(file_path):
    try:
        df = pd.read_excel(file_path, sheet_name=0)

        account_number = ''
        holder_name = ''
        closing_balance = 0.0

        for idx, row in df.iterrows():
            if 'Account Number' in str(row[1]):
                account_number = extract_account_number(row[7])
            elif 'Customer Name' in str(row[1]):
                holder_name = standardize_holder_name(row[2])
            elif 'Available Balance' in str(row[4]):
                closing_balance = clean_amount(row[5])

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
        print(f"Error parsing Equitas file {file_path.name}: {str(e)}")
        return None


def parse_bandhan_statement(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()

        account_number = ''
        holder_name = ''
        closing_balance = 0.0

        for i, line in enumerate(lines):
            if 'Full Name of Customer' in line:
                holder_name = line.split(',', 1)[1].strip() if ',' in line else ''
                holder_name = standardize_holder_name(holder_name)
            elif 'Account Number' in line:
                account_number = line.split(',', 1)[1].strip() if ',' in line else file_path.stem
            elif line.startswith('Opening Balance'):
                if i + 1 < len(lines):
                    summary_line = lines[i + 1].strip()
                    parts = summary_line.split(',')
                    if len(parts) >= 4:
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
        print(f"Error parsing Bandhan file {file_path.name}: {str(e)}")
        return None


def parse_icici_statement(file_path):
    try:
        df_raw = pd.read_excel(file_path, header=None)

        closing_balance = 0.0
        account_number = file_path.stem
        holder_name = ''

        header_row_idx = None
        balance_col_idx = None

        for idx, row in df_raw.iterrows():
            for col_idx, val in enumerate(row):
                if pd.notna(val) and 'Balance(INR)' in str(val):
                    header_row_idx = idx
                    balance_col_idx = col_idx
                    break
            if header_row_idx is not None:
                break

        for idx, row in df_raw.iterrows():
            if idx >= header_row_idx:
                break
            for val in row:
                if pd.notna(val) and 'Transactions List' in str(val):
                    parts = str(val).split('-')
                    if len(parts) >= 2:
                        holder_name = standardize_holder_name(parts[1].strip().split(',')[0])
                    break

        if header_row_idx is not None and balance_col_idx is not None:
            balance_values = df_raw[balance_col_idx].iloc[header_row_idx + 1:].dropna()
            numeric_balances = []
            for val in balance_values:
                try:
                    numeric_val = clean_amount(val)
                    if numeric_val > 0:
                        numeric_balances.append(numeric_val)
                except:
                    pass

            if numeric_balances:
                closing_balance = numeric_balances[-1]

        return {
            'bank': 'ICICI',
            'account_number': account_number,
            'holder_name': holder_name,
            'balance': closing_balance,
            'source_file': file_path.name
        }
    except Exception as e:
        print(f"Error parsing ICICI file {file_path.name}: {str(e)}")
        return None


def parse_indusind_statement(file_path):
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
        print(f"Error parsing IndusInd file {file_path.name}: {str(e)}")
        return None


def parse_kotak_statement(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()

        account_number = ''
        holder_name = ''
        closing_balance = 0.0
        transaction_start_idx = -1

        for i, line in enumerate(lines):
            if i == 1:
                holder_name = standardize_holder_name(line.strip())

            if 'Account No.' in line:
                parts = line.split(',')
                for part in parts:
                    if part.strip() and 'Account No.' not in part and part.strip() != '':
                        account_number = extract_account_number(part)
                        break

            if 'Sl. No.' in line and 'Transaction Date' in line:
                transaction_start_idx = i + 1
                break

        if transaction_start_idx > 0:
            df_transactions = pd.read_csv(file_path, skiprows=transaction_start_idx - 1)

            balance_col = None
            for col in df_transactions.columns:
                if 'Balance' in str(col):
                    balance_col = col
                    break

            if balance_col is not None:
                balance_values = df_transactions[balance_col].dropna()
                if len(balance_values) > 0:
                    closing_balance = clean_amount(balance_values.iloc[-1])

        return {
            'bank': 'Kotak Mahindra',
            'account_number': account_number,
            'holder_name': holder_name,
            'balance': closing_balance,
            'source_file': file_path.name
        }
    except Exception as e:
        print(f"Error parsing Kotak file {file_path.name}: {str(e)}")
        return None


def process_all_bank_statements():
    all_accounts = []

    print("\nProcessing bank statements\n")

    print("IDFC First Bank")
    idfc_path = BANK_PATH / 'idfc'
    if idfc_path.exists():
        for file_path in idfc_path.glob('*.xlsx'):
            result = parse_idfc_statement(file_path)
            if result:
                all_accounts.append(result)
                print(f"  {file_path.name}: {result['balance']:,.2f}")

    print("\nEquitas Bank")
    equitas_path = BANK_PATH / 'equitas'
    if equitas_path.exists():
        for file_path in equitas_path.glob('*.xlsx'):
            result = parse_equitas_statement(file_path)
            if result:
                all_accounts.append(result)
                print(f"  {file_path.name}: {result['balance']:,.2f}")

    print("\nBandhan Bank")
    bandhan_path = BANK_PATH / 'bandhan'
    if bandhan_path.exists():
        for file_path in bandhan_path.glob('*.csv'):
            result = parse_bandhan_statement(file_path)
            if result:
                all_accounts.append(result)
                print(f"  {file_path.name}: {result['balance']:,.2f}")

    print("\nICICI Bank")
    icici_path = BANK_PATH / 'icici'
    if icici_path.exists():
        for file_path in icici_path.glob('*.xlsx'):
            result = parse_icici_statement(file_path)
            if result:
                all_accounts.append(result)
                print(f"  {file_path.name}: {result['balance']:,.2f}")

    print("\nKotak Mahindra Bank")
    kotak_path = BANK_PATH / 'kotak'
    if kotak_path.exists():
        for file_path in kotak_path.glob('*.csv'):
            result = parse_kotak_statement(file_path)
            if result:
                all_accounts.append(result)
                print(f"  {file_path.name}: {result['balance']:,.2f}")

    print("\nIndusInd Bank")
    indusind_path = BANK_PATH / 'indus'
    if indusind_path.exists():
        for file_path in indusind_path.glob('*.csv'):
            result = parse_indusind_statement(file_path)
            if result:
                all_accounts.append(result)
                print(f"  {file_path.name}: {result['balance']:,.2f}")

    print(f"\nTotal accounts processed: {len(all_accounts)}\n")

    return pd.DataFrame(all_accounts)


def export_to_excel(accounts_df):
    today = datetime.now().strftime('%b\'%y')
    output_file = OUTPUT_PATH / f'Bank-Consolidated-{today}.xlsx'

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        accounts_df.to_excel(writer, sheet_name='Raw Data', index=False)

        summary = accounts_df.groupby('bank').agg({
            'balance': 'sum',
            'account_number': 'count'
        }).rename(columns={'account_number': 'num_accounts'})
        summary.to_excel(writer, sheet_name='Summary')

        ffs_data = []
        for _, row in accounts_df.iterrows():
            ffs_data.append({
                'A/c.': f"{row['bank']} - {row['holder_name']}".strip(),
                'A/c. No.': row['account_number'],
                'Balance': row['balance']
            })

        ffs_df = pd.DataFrame(ffs_data)
        ffs_df.to_excel(writer, sheet_name=f'Bank - {today}', index=False)

    print(f"Excel file created: {output_file}")
    return output_file


def save_json_for_dashboard(accounts_df):
    web_data = {
        'generated_at': datetime.now().isoformat(),
        'total_balance': float(accounts_df['balance'].sum()),
        'total_accounts': len(accounts_df),
        'banks': accounts_df.groupby('bank')['balance'].sum().to_dict(),
        'accounts': accounts_df.to_dict('records')
    }

    json_file = OUTPUT_PATH / 'bank_data.json'
    with open(json_file, 'w') as f:
        json.dump(web_data, f, indent=2)

    print(f"JSON file created: {json_file}")
    return json_file


def main():
    try:
        print("\nMeriNetWorth - Bank Data Processor")
        print(f"\nData Path: {DATA_PATH}")
        print(f"Bank Path: {BANK_PATH}")
        print(f"Output Path: {OUTPUT_PATH}")

        if not BANK_PATH.exists():
            print(f"\nError: Bank path does not exist: {BANK_PATH}")
            print("Please ensure bank statements are in the correct directory.")
            return 1

        accounts_df = process_all_bank_statements()

        if len(accounts_df) == 0:
            print("\nWarning: No accounts processed. Check your data directory.")
            return 1

        total_balance = accounts_df['balance'].sum()
        print(f"\nSUMMARY")
        print(f"Total Balance: {total_balance:,.2f}")
        print(f"Total Balance: {total_balance/100000:.2f} Lakhs")
        if total_balance >= 10000000:
            print(f"Total Balance: {total_balance/10000000:.2f} Crores")

        export_to_excel(accounts_df)
        save_json_for_dashboard(accounts_df)

        print("\nProcessing complete!")
        print("\nNext steps:")
        print("  1. Review: output/Bank-Consolidated-*.xlsx")
        print("  2. Launch dashboard: streamlit run web/app.py")

        return 0

    except Exception as e:
        print(f"\nFatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
