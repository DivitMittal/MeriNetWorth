## Project Overview

- @docs/

MeriNetWorth is a comprehensive net worth tracking system that consolidates financial data from multiple sources including bank accounts, equity holdings, mutual funds, fixed deposits, real estate, pension, and other assets. It provides visual analytics through a web dashboard.

**Supported Asset Types:**
- **Bank Accounts**: IDFC First, Equitas, Bandhan, ICICI, IndusInd, Kotak Mahindra
- **Equity Holdings**: CDSL and NSDL depositories
- **Fixed Income**: Term deposits/FDs from multiple banks
- **Real Estate**: Property valuations
- **Pension**: NPS, EPF, PPF accounts
- **Other Assets**: Cash, precious metals, etc.
- **Liabilities**: Loans, debts, receivables

**Critical Path**: Source Data → Python Parsers → JSON Output → Streamlit Dashboard

**IMPORTANT**: Never use `*Consolidated.xlsx` files in `data/` for analytics or processing. These files (e.g., `BankConsolidated.xlsx`, `EquityConsolidated.xlsx`, `MFConsolidated.xlsx`, `PensionConsolidated.xlsx`) are for personal use only and should not be parsed or integrated into the system.

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
- Returns standardized dict: `{bank, account_number, holder_name, balance, source_file}`
- Parsers registered in `PARSERS` dict for programmatic access
- All parsers must handle errors gracefully and return `None` on failure

Each depository has a dedicated parser function in `src/equity_parsers.py`:
- Returns standardized dict: `{depository, dp_id, client_id, holder_name, total_value, holdings, source_file}`
- Parsers support: `parse_cdsl_statement()` and `parse_nsdl_statement()`
- All parsers must handle errors gracefully and return `None` on failure

**Parser Pattern**:
```python
def parse_<bank>_statement(file_path: Path) -> Optional[Dict]:
    # 1. Read file (pandas)
    # 2. Extract: account_number, holder_name, closing_balance
    # 3. Return standardized dict or None on error
```

**Equity Parser Pattern**:
```python
def parse_<depository>_statement(file_path: Path) -> Optional[Dict]:
    # 1. Read file (pandas - CSV for CDSL, Excel for NSDL)
    # 2. Extract: dp_id, client_id, holder_name, holdings list
    # 3. Calculate total_value from holdings
    # 4. Return standardized dict or None on error
```

### Key Data Structures

**Account Dictionary** (returned by all parsers):
```python
{
    'bank': str,           # Bank name
    'account_number': str, # Account identifier
    'holder_name': str,    # Account holder (may be empty)
    'balance': float,      # Current balance
    'source_file': str     # Source filename
}
```

**Equity Account Dictionary** (returned by equity parsers):
```python
{
    'depository': str,     # "CDSL" or "NSDL"
    'dp_id': str,          # Depository Participant ID
    'client_id': str,      # Client ID with depository
    'holder_name': str,    # Account holder name
    'total_value': float,  # Total portfolio value
    'total_holdings': int, # Number of holdings
    'holdings': [          # List of individual holdings
        {
            'isin': str,         # Security ISIN
            'name': str,         # Security name
            'quantity': float,   # Number of units
            'last_price': float, # Last closing price
            'value': float,      # Total value (price * quantity)
            'paid_up_value': float  # Paid up value per unit
        }
    ],
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

### Kotak Mahindra Bank
- Format: CSV (.csv) with header information
- Holder name in line 1, Account number extracted from "Account No." line
- Transaction table starts after "Sl. No." and "Transaction Date" header
- Balance extracted from last transaction in balance column

### Bandhan, ICICI, IndusInd
- Generic parsers using column name matching
- Searches for column containing 'balance' (case-insensitive)
- Uses last row balance as closing balance
- Account number defaults to filename stem

## Depository-Specific Parser Notes

### CDSL (Central Depository Services Limited)
- Format: CSV (.csv) with 9-line header
- Header contains: DP ID, Client ID, Holder Name, DP Name, Statement Date, Portfolio Value
- Holdings data starts at row 10 with columns: ISIN, ISIN Name, Balance, Last Closing Price, Value
- Portfolio value extracted from "Total Portfolio Value" line using regex

### NSDL (National Securities Depository Limited)
- Format: Excel (.xlsx or .xls) with variable structure
- Metadata extraction from first 10 rows: Holder Name, DP ID, Client ID, Statement Date
- Intelligent header detection: scans for rows containing keywords (isin, security, quantity)
- Flexible column matching with expanded keywords for ISIN, name, quantity, price, value
- Fallback strategies: positional logic, first 3 non-unnamed columns
- Handles subdirectories for multiple accounts
- Calculates portfolio value from holdings if not provided

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

### Adding a New Depository

1. **Create parser in `src/equity_parsers.py`**:
```python
def parse_newdepository_statement(file_path: Path) -> Optional[Dict]:
    try:
        df = pd.read_excel(file_path)  # or pd.read_csv
        # Extract demat account details and holdings
        holdings = []
        for _, row in df.iterrows():
            holdings.append({
                'isin': extracted_isin,
                'name': extracted_name,
                'quantity': extracted_qty,
                'last_price': extracted_price,
                'value': price * qty,
                'paid_up_value': 0.0
            })

        return {
            'depository': 'NewDepository',
            'dp_id': extracted_dp_id,
            'client_id': extracted_client_id,
            'holder_name': extracted_holder_name,
            'total_value': sum(h['value'] for h in holdings),
            'total_holdings': len(holdings),
            'holdings': holdings,
            'source_file': file_path.name
        }
    except Exception as e:
        print(f"❌ Error parsing NewDepository file {file_path.name}: {str(e)}")
        return None
```

2. **Add to `process_equity.py` processing pipeline**: In `process_all_equity_statements()`, add:
```python
print("\n📊 Processing NewDepository...")
newdep_path = equity_path / 'newdepository'
if newdep_path.exists():
    for file_path in newdep_path.glob('*.xlsx'):
        result = parse_newdepository_statement(file_path)
        if result:
            all_accounts.append(result)
            print(f"  ✓ {file_path.name}: ₹{result['total_value']:,.2f}")
```

3. **Create data directory**: `data/MM.YY/Equity/newdepository/`

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
2. **Kotak parser**: Assumes standard CSV format with specific header structure
3. **NSDL parser**: Uses intelligent fallback for column detection but may fail on highly non-standard formats
4. **CDSL parser**: Expects exact 9-line header format; variations may cause parsing failures
5. **Date handling**: Assumes consistent formats, no explicit date parsing
6. **Dashboard refresh**: Requires manual refresh for new data
7. **Equity price data**: NSDL may not have price/value columns; returns 0.0 if unavailable

## File Path Configuration

All paths are configured in `src/config.py` and resolve relative to the project root:
```python
from pathlib import Path

BASE_PATH = Path(__file__).parent.parent  # Project root
DATA_PATH = BASE_PATH / 'data' / '10.25'  # Change period suffix as needed
OUTPUT_PATH = BASE_PATH / 'output'

# Period-dependent paths
BANK_PATH = DATA_PATH / 'bank'
EQUITY_PATH = DATA_PATH / 'Equity'
MF_PATH = DATA_PATH / 'MF'
REAL_ESTATE_PATH = DATA_PATH / 'real-estate'
OTHER_ASSETS_PATH = DATA_PATH / 'others'
FIXED_INCOME_PATH = DATA_PATH / 'fixed-income'
PENSION_PATH = DATA_PATH / 'pension'

# Static paths (not period-dependent)
LIABILITIES_FILE_PATH = BASE_PATH / 'data' / 'liabilities.csv'
```

**Web dashboard** uses same paths in `web/app.py`.

## Data Directory Structure

```
data/
├── liabilities.csv              # Static liabilities file
└── MM.YY/                       # Period-specific data (e.g., 10.25)
    ├── bank/                    # Bank statements
    │   ├── idfc/
    │   ├── equitas/
    │   ├── kotak/
    │   ├── bandhan/
    │   └── icici/
    ├── equity/                  # Demat statements
    │   ├── cdsl/
    │   └── nsdl/
    ├── mf/                      # Mutual fund statements
    ├── fixed-income/
    │   └── term_deposits.csv    # FD details
    ├── real-estate/
    │   └── properties.csv       # Property valuations
    ├── pension/
    │   └── pension.csv          # NPS/EPF/PPF values
    └── others/
        └── others.csv           # Other assets
```

## Asset Parsers

### Fixed Income Parser (`src/fixed_income_parser.py`)

Parses term deposit/FD data from `data/{period}/fixed-income/term_deposits.csv`.

**Expected CSV columns:**
- `S.No`, `Bank`, `FD Number`, `Amount`, `Inception Date`, `Maturity Date`
- `Maturity Instruction`, `Holders`, `Nomination`, `Interest rate`
- `Quarterly` (quarterly interest), `Interest Payout`

**Usage:**
```python
from src.fixed_income_parser import process_fixed_income, save_fixed_income_json

data = process_fixed_income()
save_fixed_income_json(data)
```

**Output structure:**
```python
{
    "generated_at": "...",
    "deposits": [...],
    "total_principal": 10000000.0,
    "total_quarterly_interest": 25000.0,
    "annual_interest_estimate": 100000.0,
    "deposit_count": 21,
    "by_bank": {"IDFC FIRST": {...}, "IndusInd": {...}}
}
```

### Real Estate Parser (`src/asset_parsers.py`)

Parses property data from `data/{period}/real-estate/properties.csv`.

**Expected CSV format:**
```csv
Name, Current Value
PROPERTY_NAME,₹ 17000000.00
```

**Usage:**
```python
from src.asset_parsers import process_real_estate, save_real_estate_json

data = process_real_estate()
save_real_estate_json(data)
```

### Other Assets Parser (`src/asset_parsers.py`)

Parses miscellaneous assets from `data/{period}/others/others.csv`.

**Expected CSV format:**
```csv
Name, Current Value
CASH,₹ 0.00
SILVER,₹ 3000000.00
```

**Usage:**
```python
from src.asset_parsers import process_other_assets, save_other_assets_json

data = process_other_assets()
save_other_assets_json(data)
```

### Pension Parser (`src/pension_parser.py`)

Parses pension account data from `data/{period}/pension/pension.csv`.

**Expected CSV format:**
```csv
Name, Type, Current Value
Ankur NPS,NPS,₹ 500000.00
Company EPF,EPF,₹ 1000000.00
```

**Usage:**
```python
from src.pension_parser import process_pension, save_pension_json

data = process_pension()
save_pension_json(data)
```

### Liability Parser (`src/liability_parser.py`)

Parses liabilities from `data/liabilities.csv` (static, not period-dependent).

**Expected CSV format:**
```csv
Date,Beneficiary,Amount (INR),Amount (Euro),Exchange Rate
2024-01-15,Loan to Friend,-50000,,
```

**Usage:**
```python
from src.liability_parser import process_all_liabilities, save_liabilities_json

data = process_all_liabilities()
save_liabilities_json(data)
```

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
- `bank_data.json`: Bank account balances
- `equity_data.json`: Equity holdings from CDSL/NSDL
- `mf_data.json`: Mutual fund holdings
- `fixed_income_data.json`: Term deposits/FDs
- `real_estate_data.json`: Property valuations
- `pension_data.json`: NPS/EPF/PPF values
- `other_assets_data.json`: Miscellaneous assets
- `liabilities_data.json`: Loans and receivables
- `networth_data.json`: Aggregated net worth

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

## Tax Computation Feature

The dashboard includes a **Tax Computation** tab that provides estimated tax calculations for each individual (identified by PAN card).

### Key Components

1. **`src/pan_config.py`** - Loads PAN registry from private config file
2. **`src/asset_aggregator.py`** - Aggregates all assets (bank, equity, MF) by PAN
3. **`src/tax_computation.py`** - Indian tax rules and computation logic
4. **`config/pan_registry.private.json`** - Private PAN data (not committed to git)
5. **`config/pan_registry.example.json`** - Example template for PAN config

### PAN Configuration

PAN mappings are stored in a private JSON file that is **not committed to git**.

**Setup:**
1. Copy `config/pan_registry.example.json` to `config/pan_registry.private.json`
2. Edit the private file with your actual PAN details

**Format** (`config/pan_registry.private.json`):
```json
{
  "ABCDE1234F": {
    "name": "Full Name",
    "name_variants": [
      "FULL NAME",
      "Full Name",
      "FULLNAME"
    ],
    "dob": "1990-01-15",
    "resident_status": "resident",
    "tax_regime": "new",
    "is_huf": false
  }
}
```

**Fields:**
- `name`: Display name for the holder
- `name_variants`: Array of name variations (as they appear in bank/demat statements)
- `dob`: Date of birth (YYYY-MM-DD) for age-based tax calculations
- `resident_status`: "resident", "non-resident", or "rnor"
- `tax_regime`: "new" or "old"
- `is_huf`: Set to `true` for HUF accounts

### Tax Rules Implemented (FY 2025-26)

**New Tax Regime Slabs:**
- Up to ₹3L: Nil
- ₹3L to ₹7L: 5%
- ₹7L to ₹10L: 10%
- ₹10L to ₹12L: 15%
- ₹12L to ₹15L: 20%
- Above ₹15L: 30%

**Capital Gains (Budget 2024):**
- LTCG on Equity/Equity MF: 12.5% (above ₹1.25L exemption)
- STCG on Equity/Equity MF: 20%
- Debt MF: Taxed at slab rate

**Other Features:**
- Standard deduction: ₹75,000 (new regime)
- Rebate u/s 87A: Up to ₹25,000 for income ≤₹7L
- Surcharge: 10-37% based on income
- Health & Education Cess: 4%

### Important Notes

- Tax computations are **ESTIMATES** based on current asset holdings
- Actual tax depends on realized gains, other income sources, and deductions
- Interest income is estimated at 4% annual rate on bank balances
- Capital gains shown are unrealized (for informational purposes only)

## Future Enhancements Planned

- Equity holdings integration (`data/MM.YY/Equity/`)
- Mutual fund statement parsing
- FD maturity tracking and alerts
- Historical trend analysis (month-over-month)
- Unit tests for parsers (currently none exist)
