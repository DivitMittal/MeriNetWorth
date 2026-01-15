# MeriNetWorth

[![Flake Check](https://github.com/DivitMittal/MeriNetWorth/actions/workflows/flake-check.yml/badge.svg)](https://github.com/DivitMittal/MeriNetWorth/actions/workflows/flake-check.yml)
[![Flake Lock Update](https://github.com/DivitMittal/MeriNetWorth/actions/workflows/flake-lock-update.yml/badge.svg)](https://github.com/DivitMittal/MeriNetWorth/actions/workflows/flake-lock-update.yml)

Personal net worth tracking system that consolidates financial data from multiple sources (bank accounts, equity holdings, mutual funds) and provides comprehensive visual analytics through an interactive web dashboard.

## 1. Overview

This repository contains tools for extracting, consolidating, and visualizing personal financial data across multiple asset classes:

- **Bank Accounts:** Savings accounts from IDFC First, Equitas, Bandhan, ICICI, IndusInd, Kotak Mahindra
- **Equity Holdings:** Demat account holdings from CDSL and NSDL depositories
- **Mutual Funds:** MF Central (Karvy/CAMS) statement of accounts (SOA)

The system employs a two-phase architecture:

- **Data Extraction:** Python-based parsers that extract standardized information from institution-specific statement formats (Excel, CSV, PDF)
- **Data Visualization:** Streamlit-powered web dashboard with tabbed interface, interactive charts, filtering, and Indian currency formatting (Lakhs/Crores)

### Key Features

✅ **Multi-Asset Tracking**: Banks, equity, and mutual funds in one unified dashboard
✅ **Comprehensive Account Info**: Account numbers, first/second holders, and nominee details
✅ **Smart Parsing**: Bank-specific extractors with improved reliability for Equitas, ICICI, and Kotak
✅ **Visual Analytics**: Interactive charts (pie, bar, treemap, box plot) with Indian currency formatting
✅ **Tabbed Interface**: Separate views for Banks, Equity, and Mutual Funds
✅ **Performance Tracking**: MF returns calculation with color-coded gain/loss indicators
✅ **Secure Access**: Password-protected dashboard with dark mode support
✅ **Real-time Updates**: Equity price sync integration with Upstox API

## 2. Project Structure

```
/
├── data/
│   └── MM.YY/                        # Monthly data folders (e.g., 10.25)
│       ├── Bank/                     # Bank statements by institution
│       │   ├── IDFCFirst/
│       │   ├── Equitas/
│       │   ├── Bandhan/
│       │   ├── ICICI/
│       │   ├── IndusInd/
│       │   └── Kotak/
│       ├── Equity/                   # Equity holdings data
│       │   ├── cdsl/                 # CDSL demat statements
│       │   └── nsdl/                 # NSDL demat statements
│       └── MF/                       # Mutual fund statements
│           └── mfcentral/            # MF Central (CAMS/Karvy) PDFs
├── src/                              # Source modules
│   ├── bank_parsers.py               # Bank-specific parsing functions
│   ├── equity_parsers.py             # CDSL/NSDL demat statement parsers
│   ├── mf_parsers.py                 # Mutual fund statement parsers
│   ├── process_banks.py              # Bank processing orchestration
│   ├── process_equity.py             # Equity processing logic
│   └── process_mf.py                 # Mutual fund processing logic
├── web/
│   └── app.py                        # Streamlit dashboard application
├── tests/                            # Test suite
│   ├── test_parsers.py               # Bank parser tests
│   └── test_equity.py                # Equity parser tests
├── scripts/
│   └── debug/                        # Debug/inspection utilities
├── output/                           # Generated reports
│   ├── bank_data.json                # Bank account data (JSON)
│   ├── equity_data.json              # Equity holdings data (JSON)
│   ├── mf_data.json                  # Mutual fund data (JSON)
│   ├── networth_data.json            # Combined net worth data (JSON)
│   └── Bank-Consolidated-*.xlsx      # Excel consolidated report
├── process_all.py                    # Main entry point
├── run_dashboard.sh                  # Dashboard launcher script
├── requirements.txt                  # Python dependencies
└── README.md                         # This file
```

## 3. Dataset

The system processes financial data from three main sources:

- **Bank Statements** (`data/MM.YY/Bank/`): Organized by bank name, containing Excel/CSV statement exports
- **Equity Holdings** (`data/MM.YY/Equity/`): CDSL CSV files and NSDL Excel files with demat holdings
- **Mutual Funds** (`data/MM.YY/MF/`): MF Central PDF statements from CAMS/Karvy

All financial data is sensitive and excluded from version control via `.gitignore`.

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

### 4.4. Web Dashboard

- **File:** `web/app.py`
- **Description:** Interactive Streamlit dashboard with tabbed interface providing:

  **Summary Metrics:**
  - Total Net Worth (combined across all asset types)
  - Bank Balance, Equity Value, Mutual Fund Value
  - Account/holdings count by asset type

  **🏦 Banks Tab:**
  - Bank-wise filtering and account summaries
  - Visual analytics: Pie charts, sunburst, bar charts, treemaps, box plots
  - Detailed account information with holder and nominee details
  - Account details table with First Holder, Second Holder, and Nominee columns

  **📈 Equity Tab:**
  - Top holdings table with current valuations
  - Portfolio distribution charts
  - Holdings breakdown by depository (CDSL/NSDL)
  - Price sync integration with Upstox API

  **💰 Mutual Funds Tab:**
  - Top MF holdings with returns calculation
  - Performance charts showing gain/loss percentage
  - Holdings breakdown by PAN/account
  - Color-coded gain/loss indicators

  **Other Features:**
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
- Parse bank statements from `data/MM.YY/Bank/`
- Parse equity holdings from `data/MM.YY/Equity/`
- Parse mutual fund statements from `data/MM.YY/MF/`
- Extract account balances, portfolio valuations, and MF holdings
- Generate JSON files: `bank_data.json`, `equity_data.json`, `mf_data.json`, `networth_data.json`
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
- [ ] Historical trend analysis (month-over-month comparisons)
- [ ] Email report generation with portfolio summary
- [ ] Automated monthly processing with scheduled runs
- [ ] FD maturity tracking and alerts
- [ ] Real-time equity price updates (beyond Upstox)
- [ ] Asset allocation analysis and rebalancing suggestions
- [ ] Tax harvesting recommendations (LTCG/STCG)
- [ ] Goal-based tracking (retirement, education, etc.)
