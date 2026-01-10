# MeriNetWorth

[![Flake Check](https://github.com/DivitMittal/MeriNetWorth/actions/workflows/flake-check.yml/badge.svg)](https://github.com/DivitMittal/MeriNetWorth/actions/workflows/flake-check.yml)
[![Flake Lock Update](https://github.com/DivitMittal/MeriNetWorth/actions/workflows/flake-lock-update.yml/badge.svg)](https://github.com/DivitMittal/MeriNetWorth/actions/workflows/flake-lock-update.yml)

Personal net worth tracking system that consolidates bank account data from multiple Indian banks and provides visual analytics through an interactive web dashboard.

## 1. Overview

This repository contains tools for extracting, consolidating, and visualizing personal financial data across multiple bank accounts. The system processes statements from various Indian banks and generates consolidated reports with interactive visualizations.

The system employs a two-phase architecture:

- **Data Extraction:** Python-based parsers that extract account information from bank-specific statement formats (Excel, CSV)
- **Data Visualization:** Streamlit-powered web dashboard with interactive charts, filtering, and Indian currency formatting (Lakhs/Crores)

## 2. Project Structure

```
/
├── data/
│   └── MM.YY/                        # Monthly data folders (e.g., 06.25)
│       ├── Bank/                     # Bank statements by institution
│       │   ├── IDFCFirst/
│       │   ├── Equitas/
│       │   ├── Bandhan/
│       │   ├── ICICI/
│       │   ├── IndusInd/
│       │   └── Kotak/
│       └── Equity/                   # Equity holdings data
│           ├── cdsl/                 # CDSL demat statements
│           └── nsdl/                 # NSDL demat statements
├── src/                              # Source modules
│   ├── bank_parsers.py               # Bank-specific parsing functions
│   ├── equity_parsers.py             # CDSL/NSDL demat statement parsers
│   ├── process_banks.py              # Bank processing orchestration
│   └── process_equity.py             # Equity processing logic
├── web/
│   └── app.py                        # Streamlit dashboard application
├── tests/                            # Test suite
│   ├── test_parsers.py               # Bank parser tests
│   └── test_equity.py                # Equity parser tests
├── scripts/
│   └── debug/                        # Debug/inspection utilities
├── output/                           # Generated reports
│   ├── bank_data.json                # JSON data for web dashboard
│   └── Bank-Consolidated-*.xlsx      # Excel consolidated report
├── process_all.py                    # Main entry point
├── run_dashboard.sh                  # Dashboard launcher script
├── requirements.txt                  # Python dependencies
└── README.md                         # This file
```

## 3. Dataset

The system processes bank statements stored in `data/MM.YY/Bank/` directories, organized by bank name. Each bank folder contains statement files in their native export format (Excel or CSV). The data is sensitive financial information and is excluded from version control via `.gitignore`.

## 4. Components

### 4.1. Bank Parsers

- **File:** `src/bank_parsers.py`
- **Description:** Contains bank-specific parsing functions that extract standardized account information from various statement formats:
  - Account number extraction
  - Account holder name identification
  - Closing balance calculation
  - Source file tracking
- **Supported Banks:** IDFC First, Equitas, Bandhan, ICICI, IndusInd, Kotak Mahindra

| Bank | Format | Key Fields Extracted |
|------|--------|---------------------|
| IDFC First | Excel (.xlsx) | Account No, Holder, Balance, FD |
| Equitas | Excel (.xlsx) | Account No, Holder, Balance |
| Bandhan | CSV (.csv) | Balance |
| ICICI | Excel (.xls) | Balance |
| IndusInd | CSV (.csv) | Balance |
| Kotak Mahindra | CSV (.csv) | Account No, Holder, Balance |

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

### 4.3. Web Dashboard

- **File:** `web/app.py`
- **Description:** Interactive Streamlit dashboard providing:
  - **Metric Cards:** Total balance, average balance, highest balance
  - **Bank Filter:** Select specific banks to view
  - **Visual Analytics:** Pie charts, bar charts, treemaps, box plots
  - **Currency Formatting:** Indian number system (Lakhs/Crores)
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

### 5.2. Process Bank Data

```bash
python process_all.py
```

This will:
- Parse bank statements from `data/MM.YY/Bank/`
- Parse equity holdings from `data/MM.YY/Equity/`
- Extract account balances and portfolio valuations
- Generate `output/bank_data.json` and `output/equity_data.json`
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

1. Download new statements to `data/MM.YY/Bank/`
2. Update `DATA_PATH` in processor if needed
3. Run `python process_all.py`
4. Dashboard auto-loads new data

## 7. Future Enhancements

- [ ] Mutual fund statement parsing
- [ ] Historical trend analysis
- [ ] Email report generation
- [ ] Automated monthly processing
- [ ] FD maturity tracking and alerts
