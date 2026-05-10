# MeriNetWorth

[![Flake Check](https://github.com/DivitMittal/MeriNetWorth/actions/workflows/flake-check.yml/badge.svg)](https://github.com/DivitMittal/MeriNetWorth/actions/workflows/flake-check.yml)
[![Flake Lock Update](https://github.com/DivitMittal/MeriNetWorth/actions/workflows/flake-lock-update.yml/badge.svg)](https://github.com/DivitMittal/MeriNetWorth/actions/workflows/flake-lock-update.yml)

Personal net worth tracking system that consolidates financial data from multiple sources (bank accounts, equity holdings, mutual funds, fixed deposits, real estate, pension, and other assets) and provides comprehensive visual analytics through an interactive web dashboard.

## 1. Overview

This repository contains tools for extracting, consolidating, and visualizing personal financial data across multiple asset classes:

- **Bank Accounts:** Savings accounts from IDFC First, Equitas, Bandhan, ICICI, IndusInd, Kotak Mahindra
- **Equity Holdings:** Demat account holdings from CDSL and NSDL depositories
- **Mutual Funds:** MF Central (Karvy/CAMS) statement of accounts (SOA)
- **Fixed Income:** Term deposits/FDs from multiple banks
- **Real Estate:** Property valuations
- **Pension:** NPS, EPF, PPF accounts
- **Other Assets:** Cash, precious metals, etc.
- **Liabilities:** Loans, debts, and receivables

The system employs a two-phase architecture:

- **Data Extraction:** Python-based parsers that extract standardized information from institution-specific statement formats (Excel, CSV, PDF)
- **Data Visualization:** Streamlit-powered web dashboard with tabbed interface, interactive charts, filtering, and Indian currency formatting (Lakhs/Crores)

### Key Features

✅ **Multi-Asset Tracking**: Banks, equity, mutual funds, FDs, real estate, pension, and more
✅ **Comprehensive Account Info**: Account numbers, first/second holders, and nominee details
✅ **Smart Parsing**: Bank-specific extractors with improved reliability for Equitas, ICICI, and Kotak
✅ **Visual Analytics**: Interactive charts (pie, bar, treemap, box plot) with Indian currency formatting
✅ **Tabbed Interface**: Separate views for Banks, Equity, Mutual Funds, and other assets
✅ **Performance Tracking**: MF returns calculation with color-coded gain/loss indicators
✅ **Secure Access**: Password-protected dashboard with dark mode support
✅ **Real-time Updates**: Equity price sync integration with Upstox API
✅ **Liabilities Tracking**: Net worth calculation accounting for debts and receivables

## 2. Project Structure

```
/
├── data/
│   ├── liabilities.csv              # Static liabilities file
│   └── MM.YY/                       # Monthly data folders (e.g., 10.25)
│       ├── bank/                    # Bank statements by institution
│       │   ├── idfc/
│       │   ├── equitas/
│       │   ├── bandhan/
│       │   ├── icici/
│       │   ├── indusind/
│       │   └── kotak/
│       ├── equity/                  # Equity holdings data
│       │   ├── cdsl/                # CDSL demat statements
│       │   └── nsdl/                # NSDL demat statements
│       ├── mf/                      # Mutual fund statements
│       │   └── mfcentral/           # MF Central (CAMS/Karvy) PDFs
│       ├── fixed-income/
│       │   └── term_deposits.csv    # FD/term deposit details
│       ├── real-estate/
│       │   └── properties.csv       # Property valuations
│       ├── pension/
│       │   └── pension.csv          # NPS/EPF/PPF values
│       └── others/
│           └── others.csv           # Other assets (cash, metals, etc.)
├── src/                             # Source modules
│   ├── bank_parsers.py              # Bank-specific parsing functions
│   ├── equity_parsers.py            # CDSL/NSDL demat statement parsers
│   ├── mf_parsers.py                # Mutual fund statement parsers
│   ├── fixed_income_parser.py       # Term deposit/FD parser
│   ├── asset_parsers.py             # Real estate and other assets parser
│   ├── pension_parser.py            # Pension (NPS/EPF/PPF) parser
│   ├── liability_parser.py          # Liabilities parser
│   ├── config.py                    # Centralized path configuration
│   ├── process_banks.py             # Bank processing orchestration
│   ├── process_equity.py            # Equity processing logic
│   └── process_mf.py                # Mutual fund processing logic
├── web/
│   └── app.py                       # Streamlit dashboard application
├── tests/                           # Test suite
│   ├── test_parsers.py              # Bank parser tests
│   └── test_equity.py               # Equity parser tests
├── config/                          # Configuration files
│   ├── pan_registry.example.json    # PAN config template
│   └── pan_registry.private.json    # Private PAN data (git-ignored)
├── output/                          # Generated reports
│   ├── bank_data.json               # Bank account data
│   ├── equity_data.json             # Equity holdings data
│   ├── mf_data.json                 # Mutual fund data
│   ├── fixed_income_data.json       # Term deposit data
│   ├── real_estate_data.json        # Real estate data
│   ├── pension_data.json            # Pension data
│   ├── other_assets_data.json       # Other assets data
│   ├── liabilities_data.json        # Liabilities data
│   └── networth_data.json           # Combined net worth data
├── process_all.py                   # Main entry point
├── run_dashboard.sh                 # Dashboard launcher script
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## 3. Dataset

The system processes financial data from multiple sources:

- **Bank Statements** (`data/MM.YY/bank/`): Organized by bank name, containing Excel/CSV statement exports
- **Equity Holdings** (`data/MM.YY/equity/`): CDSL CSV files and NSDL Excel files with demat holdings
- **Mutual Funds** (`data/MM.YY/mf/`): MF Central PDF statements from CAMS/Karvy
- **Fixed Income** (`data/MM.YY/fixed-income/term_deposits.csv`): Term deposit details with maturity tracking
- **Real Estate** (`data/MM.YY/real-estate/properties.csv`): Property valuations
- **Pension** (`data/MM.YY/pension/pension.csv`): NPS, EPF, PPF account values
- **Other Assets** (`data/MM.YY/others/others.csv`): Cash, precious metals, etc.
- **Liabilities** (`data/liabilities.csv`): Static file for loans and receivables

All financial data is sensitive and excluded from version control via `.gitignore`.

**IMPORTANT**: Never use `*Consolidated.xlsx` files in `data/` for analytics. These are for personal use only.

## 4. Components

### 4.1. Bank Parsers

- **File:** `src/bank_parsers.py`
- **Description:** Contains bank-specific parsing functions that extract standardized account information from various statement formats:
  - Account number extraction (with improved reliability for Equitas, ICICI, Kotak)
  - Account holder information (first holder, second holder)
  - Nominee details
  - Closing balance calculation
  - Source file tracking
- **Supported Banks:** IDFC First, Equitas, Bandhan, ICICI, IndusInd, Kotak Mahindra

| Bank | Format | Key Fields Extracted |
|------|--------|---------------------|
| IDFC First | Excel (.xlsx) | Account No, Holder, Balance |
| Equitas | Excel (.xlsx) | Account No, First Holder, Second Holder, Nominee, Balance |
| Bandhan | CSV (.csv) | Balance (Account No from filename) |
| ICICI | Excel (.xls) | Account No, First Holder, Second Holder, Balance |
| IndusInd | CSV (.csv) | Balance (Account No from filename) |
| Kotak Mahindra | CSV (.csv) | Account No, First Holder, Second Holder, Nominee, Balance |

### 4.2. Equity Parsers

- **File:** `src/equity_parsers.py`
- **Description:** Contains depository-specific parsing functions for equity holdings:
  - ISIN identification and security name extraction
  - Quantity and valuation parsing
  - Portfolio value calculation
  - Holder information extraction
- **Supported Depositories:** CDSL, NSDL

| Depository | Format | Key Fields Extracted |
|------------|--------|---------------------|
| CDSL | CSV (.csv) | DP ID, Client ID, Holder Name, Holdings (ISIN, Quantity, Price, Value) |
| NSDL | Excel (.xlsx/.xls) | DP ID, Client ID, Holder Name, Holdings (ISIN, Quantity, Price, Value) |

### 4.3. Mutual Fund Parsers

- **File:** `src/mf_parsers.py`
- **Description:** Parses MF Central (CAMS/Karvy) consolidated account statements:
  - PAN and holder information extraction
  - Folio number identification
  - Scheme name and NAV parsing
  - Units and market value calculation
  - Invested value tracking for returns calculation
- **Supported Platforms:** MF Central (CAMS/Karvy combined PDFs)

| Platform | Format | Key Fields Extracted |
|----------|--------|---------------------|
| MF Central | PDF (.pdf) | PAN, Holder Name, Folios, Scheme Names, Units, NAV, Market Value, Invested Value |

### 4.4. Fixed Income Parser

- **File:** `src/fixed_income_parser.py`
- **Description:** Parses term deposit/FD data:
  - FD number and bank identification
  - Principal amount and interest rate
  - Inception and maturity dates
  - Quarterly interest calculation
  - Holder and nominee information

| Source | Format | Key Fields Extracted |
|--------|--------|---------------------|
| Term Deposits | CSV (.csv) | Bank, FD Number, Amount, Interest Rate, Maturity Date, Holders, Quarterly Interest |

### 4.5. Asset Parsers

- **File:** `src/asset_parsers.py`
- **Description:** Parses real estate and other miscellaneous assets:
  - Property name and current valuation
  - Asset categorization
  - Simple Name/Value CSV format

| Asset Type | Format | Key Fields Extracted |
|------------|--------|---------------------|
| Real Estate | CSV (.csv) | Property Name, Current Value |
| Other Assets | CSV (.csv) | Asset Name, Current Value |

### 4.6. Pension Parser

- **File:** `src/pension_parser.py`
- **Description:** Parses pension account data:
  - Account holder identification
  - Pension type (NPS, EPF, PPF)
  - Current corpus value

| Source | Format | Key Fields Extracted |
|--------|--------|---------------------|
| Pension | CSV (.csv) | Name, Type (NPS/EPF/PPF), Current Value |

### 4.7. Liability Parser

- **File:** `src/liability_parser.py`
- **Description:** Parses liabilities (loans, debts, receivables):
  - Beneficiary identification
  - Amount tracking (INR and foreign currency)
  - Net liability/receivable calculation

| Source | Format | Key Fields Extracted |
|--------|--------|---------------------|
| Liabilities | CSV (.csv) | Date, Beneficiary, Amount (INR), Amount (Euro), Exchange Rate |

### 4.8. Web Dashboard

- **File:** `web/app.py`
- **Description:** Interactive Streamlit dashboard with tabbed interface providing:

  - **Summary Metrics:**
    - Total Net Worth (combined across all asset types)
    - Bank Balance, Equity Value, Mutual Fund Value
    - Account/holdings count by asset type

  - **🏦 Banks Tab:**
    - Bank-wise filtering and account summaries
    - Visual analytics: Pie charts, sunburst, bar charts, treemaps, box plots
    - Detailed account information with holder and nominee details
    - Account details table with First Holder, Second Holder, and Nominee columns

  - **📈 Equity Tab:**
    - Top holdings table with current valuations
    - Portfolio distribution charts
    - Holdings breakdown by depository (CDSL/NSDL)
    - Price sync integration with Upstox API

  - **💰 Mutual Funds Tab:**
    - Top MF holdings with returns calculation
    - Performance charts showing gain/loss percentage
    - Holdings breakdown by PAN/account
    - Color-coded gain/loss indicators

  - **Other Features:**
    - Currency formatting in Indian number system (Lakhs/Crores)
    - Password-protected access
    - Dark mode optimized UI

- **Dependencies:** Streamlit, Plotly, Pandas

## 5. Quick Start

### 5.1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or with uv:
```bash
uv sync
```

### 5.2. Process Financial Data

```bash
python process_all.py
```

This will:
- Parse bank statements from `data/MM.YY/bank/`
- Parse equity holdings from `data/MM.YY/equity/`
- Parse mutual fund statements from `data/MM.YY/mf/`
- Parse fixed income from `data/MM.YY/fixed-income/`
- Parse real estate from `data/MM.YY/real-estate/`
- Parse pension data from `data/MM.YY/pension/`
- Parse other assets from `data/MM.YY/others/`
- Parse liabilities from `data/liabilities.csv`
- Generate JSON files for each asset type in `output/`
- Create consolidated Excel reports

### 5.3. Launch Web Dashboard

```bash
./run_dashboard.sh
```

Or manually:
```bash
streamlit run web/app.py
```

The dashboard opens at `http://localhost:8501`

## 6. Extending the System

### 6.1. Adding New Banks

1. Create a parser function in `src/bank_parsers.py`:
```python
def parse_newbank_statement(file_path: Path) -> Optional[Dict]:
    try:
        df = pd.read_excel(file_path)
        # Extract account details from bank-specific format
        return {
            'bank': 'NewBank',
            'account_number': extracted_account_no,
            'holder_name': extracted_holder_name,
            'first_holder': extracted_first_holder,
            'second_holder': extracted_second_holder,  # Empty string if none
            'nominee': extracted_nominee,  # Empty string if none
            'balance': extracted_balance,
            'source_file': file_path.name
        }
    except Exception as e:
        print(f"❌ Error parsing NewBank: {e}")
        return None
```

2. Register in the `PARSERS` dict and add to the processing pipeline

3. Create data directory: `data/MM.YY/Bank/NewBank/`

### 6.2. Monthly Updates

1. Download new statements:
   - Bank statements to `data/MM.YY/Bank/`
   - Equity holdings to `data/MM.YY/Equity/`
   - Mutual fund PDFs to `data/MM.YY/MF/`
2. Update `DATA_PATH` in processor if needed (change month/year)
3. Run `python process_all.py`
4. Dashboard auto-loads new data from updated JSON files

## 7. Future Enhancements

- [x] ~~Mutual fund statement parsing~~ (Completed - MF Central PDF parsing)
- [x] ~~Equity holdings tracking~~ (Completed - CDSL/NSDL)
- [x] ~~Holder and nominee information~~ (Completed - Bank parsers)
- [x] ~~Fixed deposit tracking~~ (Completed - Term deposits parser)
- [x] ~~Real estate valuation~~ (Completed - Properties parser)
- [x] ~~Pension tracking~~ (Completed - NPS/EPF/PPF parser)
- [x] ~~Liabilities tracking~~ (Completed - Loans and receivables)
- [x] Historical trend analysis (month-over-month comparisons)
- [ ] Automated monthly processing with scheduled runs
- [x] FD maturity tracking and alerts
- [x] Real-time equity price updates (via Upstox sync)
- [x] Asset allocation analysis and rebalancing suggestions
- [x] Tax harvesting recommendations (based on available cost-basis data)
- [x] Goal-based tracking (via optional `data/goals.csv`)

### Planning Configuration

The dashboard includes a Planning tab backed by `output/planning_data.json` and `output/history_data.json`.

Optional target allocations can be configured in `data/planning.json`:

```json
{
  "target_allocation": {
    "bank_balance": 10,
    "equity_value": 35,
    "mf_value": 25,
    "fixed_income_value": 20,
    "real_estate_value": 10
  }
}
```

Optional goals can be configured in `data/goals.csv`:

```csv
Name,Target Amount,Current Amount,Target Date
Retirement,50000000,,2045-12-31
```

If these files are absent, the dashboard shows safe “not configured” empty states.
