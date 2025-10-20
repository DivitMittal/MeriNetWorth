# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MeriNetWorth is a bank account consolidation system that extracts data from multiple bank statement formats and provides visual analytics through a web dashboard. The system processes statements from IDFC First, Equitas, Bandhan, ICICI, and IndusInd banks.

**Critical Path**: Bank Statements → Jupyter Notebook → [Excel + JSON] → Streamlit Dashboard

## Development Commands

### Setup
```bash
pip install -r requirements.txt
```

### Data Processing
```bash
# Primary workflow: Launch Jupyter notebook
jupyter notebook notebooks/bank_data_processor.ipynb
# Then: Cell → Run All (or Shift+Enter per cell)
```

### Web Dashboard
```bash
# Quick launcher (recommended)
./run_dashboard.sh

# Manual launch
streamlit run web/app.py
# Opens at http://localhost:8501
```

## Architecture & Data Flow

### Two-Phase Architecture

**Phase 1: Data Extraction (Jupyter)**
- Input: Bank statements in `data/MM.YY/Bank/{BankName}/`
- Process: Bank-specific parsers extract account info
- Output: `output/bank_data.json` + `output/Bank-Consolidated-*.xlsx`

**Phase 2: Visualization (Streamlit)**
- Input: `output/bank_data.json`
- Process: Load, filter, and render interactive charts
- Output: Web dashboard at localhost:8501

### Parser Architecture

Each bank has a dedicated parser function in `src/bank_parsers.py`:
- Returns standardized dict: `{bank, account_number, holder_name, balance, fd_amount, source_file}`
- Parsers registered in `PARSERS` dict for programmatic access
- All parsers must handle errors gracefully and return `None` on failure

**Parser Pattern**:
```python
def parse_<bank>_statement(file_path: Path) -> Optional[Dict]:
    # 1. Read file (pandas)
    # 2. Extract: account_number, holder_name, closing_balance
    # 3. Return standardized dict or None on error
```

### Key Data Structures

**Account Dictionary** (returned by all parsers):
```python
{
    'bank': str,           # Bank name
    'account_number': str, # Account identifier
    'holder_name': str,    # Account holder (may be empty)
    'balance': float,      # Current balance
    'fd_amount': float,    # Fixed deposit amount (currently 0.0)
    'source_file': str     # Source filename
}
```

**JSON Output** (`output/bank_data.json`):
```python
{
    'generated_at': str,        # ISO datetime
    'total_balance': float,     # Sum of all balances
    'total_accounts': int,      # Account count
    'banks': dict,              # {bank_name: total_balance}
    'accounts': list[dict]      # List of account dicts
}
```

**Excel Output** (3 sheets):
1. "Raw Data": All account records
2. "Summary": Aggregated by bank
3. "Bank - Jun'25": FFS-compatible format

## Bank-Specific Parser Notes

### IDFC First Bank
- Format: Excel (.xlsx) with "Account Statement" sheet
- Extracts from header rows: ACCOUNT NUMBER, CUSTOMER NAME, Closing Balance
- Balance in 4th column (index 3) of "Closing Balance" row

### Equitas Small Finance Bank
- Format: Excel (.xlsx), sheet index 0
- Account Number in row[7], Customer Name in row[2]
- Fallback: If balance not in header, scans last transactions backward

### Bandhan, ICICI, IndusInd
- Generic parsers using column name matching
- Searches for column containing 'balance' (case-insensitive)
- Uses last row balance as closing balance
- Account number defaults to filename stem

## Extending the System

### Adding a New Bank

1. **Create parser in `src/bank_parsers.py`**:
```python
def parse_newbank_statement(file_path: Path) -> Optional[Dict]:
    try:
        df = pd.read_excel(file_path)  # or pd.read_csv
        # Extract account details
        return {
            'bank': 'NewBank',
            'account_number': extracted_account_no,
            'holder_name': extracted_holder_name,
            'balance': extracted_balance,
            'fd_amount': 0.0,
            'source_file': file_path.name
        }
    except Exception as e:
        print(f"❌ Error parsing NewBank file {file_path.name}: {str(e)}")
        return None
```

2. **Register in `PARSERS` dict**:
```python
PARSERS = {
    'newbank': parse_newbank_statement,
    # ... existing parsers
}
```

3. **Add to notebook processing pipeline**: In `process_all_bank_statements()`, add:
```python
print("\n📊 Processing NewBank...")
for file_path in BANK_PATH.glob('NewBank/*.xlsx'):
    result = parse_newbank_statement(file_path)
    if result:
        all_accounts.append(result)
        print(f"  ✓ {file_path.name}: ₹{result['balance']:,.2f}")
```

4. **Create data directory**: `data/MM.YY/Bank/NewBank/`

### Monthly Data Updates

1. Download new bank statements to `data/MM.YY/Bank/`
2. Update `DATA_PATH` in notebook: `DATA_PATH = BASE_PATH / 'data' / 'MM.YY'`
3. Run all notebook cells
4. Dashboard auto-loads new `bank_data.json`

## Critical Implementation Details

### Currency Formatting
- Web dashboard uses `format_currency()` for Indian formatting (Lakhs/Crores)
- Threshold: ≥1 Crore shows as "₹X.XX Cr", ≥1 Lakh as "₹X.XX L"

### Data Security
- `.gitignore` excludes: `data/`, `output/`, `*.csv`, `*.xlsx`, `*.xls`
- All processing is local (no cloud uploads)
- Bank statements contain sensitive financial information

### Dashboard Dependencies
- Dashboard requires `output/bank_data.json` to exist
- If missing, shows error: "No data found! Please run the Jupyter notebook first"
- Dashboard caches data with `@st.cache_data` decorator

### Known Limitations
1. **Bandhan/ICICI/IndusInd parsers**: Use filename as account number (not extracted from file)
2. **Date handling**: Assumes consistent formats, no explicit date parsing
3. **FD amounts**: Currently hardcoded to 0.0 (future enhancement)
4. **Dashboard refresh**: Requires manual refresh for new data

## File Path Configuration

All paths relative to project root:
```python
BASE_PATH = Path('/Users/div/Projects/MeriNetWorth')
DATA_PATH = BASE_PATH / 'data' / '06.25'  # Change period here
BANK_PATH = DATA_PATH / 'Bank'
OUTPUT_PATH = BASE_PATH / 'output'
```

**Web dashboard** uses same paths in `web/app.py`.

## Troubleshooting Common Issues

### "No data found" in Dashboard
- **Cause**: `output/bank_data.json` doesn't exist
- **Fix**: Run Jupyter notebook to generate data files

### Parser Fails with KeyError/IndexError
- **Cause**: Bank statement format changed or unexpected structure
- **Fix**: Add debug prints in parser to inspect DataFrame structure, adjust row/column indices

### Excel Export Fails
- **Cause**: Missing openpyxl dependency
- **Fix**: `pip install openpyxl`

### Charts Don't Display
- **Cause**: Missing plotly dependency
- **Fix**: `pip install plotly`

## Output Files

### Generated Files (in `output/`)
- `bank_data.json`: Web dashboard data source
- `Bank-Consolidated-Jun'25.xlsx`: Excel report (3 sheets)

### Expected Console Output Pattern
```
🏦 PROCESSING ALL BANK STATEMENTS
📊 Processing <Bank Name>...
  ✓ <filename>: ₹<balance>
✅ Total accounts processed: <N>
🎯 TOTAL BALANCE: ₹<amount> Lakhs
✅ Excel file created: output/Bank-Consolidated-Jun'25.xlsx
✅ JSON file created: output/bank_data.json
```

## Future Enhancements Planned

- Equity holdings integration (`data/MM.YY/Equity/`)
- Mutual fund statement parsing
- FD maturity tracking and alerts
- Historical trend analysis (month-over-month)
- Unit tests for parsers (currently none exist)
