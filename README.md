# MeriNetWorth - Bank Account Consolidation System

A comprehensive solution to extract, consolidate, and visualize bank account data from multiple sources.

## Features

- **Multi-Bank Support**: Automatically parse statements from IDFC First, Equitas, Bandhan, ICICI, and IndusInd banks
- **Data Processing**: Python scripts for automated statement processing
- **Web Dashboard**: Beautiful Streamlit-based visualization interface
- **Analytics**: Charts, graphs, and insights into your financial data
- **Excel Export**: Generate consolidated reports

## Project Structure

```
MeriNetWorth/
├── data/
│   └── MM.YY/              # Monthly data folders
│       ├── Bank/           # Bank statements by institution
│       │   ├── IDFCFirst/
│       │   ├── Equitas/
│       │   ├── Bandhan/
│       │   ├── ICICI/
│       │   └── IndusInd/
│       └── equity/         # Equity holdings data
├── src/                    # Source modules
│   ├── bank_parsers.py     # Bank-specific parsers
│   ├── process_banks.py    # Bank processing logic
│   └── process_equity.py   # Equity processing logic
├── web/
│   └── app.py              # Streamlit dashboard
├── output/                 # Generated reports
│   ├── bank_data.json      # JSON data for web
│   └── Bank-Consolidated-*.xlsx
├── process_all.py          # Main entry point
├── requirements.txt        # Python dependencies
└── README.md
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or with uv:
```bash
uv sync
```

### 2. Process Bank Data

Run the data processor:

```bash
python process_all.py
```

This will:
- Parse bank statements from various formats
- Extract current balances
- Generate consolidated Excel reports
- Create JSON data for web visualization

### 3. Launch Web Dashboard

```bash
./run_dashboard.sh
```

Or manually:
```bash
streamlit run web/app.py
```

The dashboard will open in your browser at `http://localhost:8501`

## Web Dashboard Features

### Main Dashboard

- **Metric Cards**: Total balance, average balance, highest balance
- **Bank Filter**: Select specific banks to view
- **Visual Analytics**:
  - Pie charts for distribution
  - Bar charts for comparison
  - Treemaps for hierarchy
  - Box plots for distribution analysis

### Interactive Features

- Real-time filtering by bank
- Expandable bank sections with account details
- Responsive design for mobile and desktop
- Color-coded visualizations
- Currency formatting (Lakhs/Crores)

## Supported Bank Formats

| Bank | Format | Key Fields Extracted |
|------|--------|---------------------|
| IDFC First | Excel (.xlsx) | Account No, Holder, Balance, FD |
| Equitas | Excel (.xlsx) | Account No, Holder, Balance |
| Bandhan | CSV (.csv) | Balance |
| ICICI | Excel (.xls) | Balance |
| IndusInd | CSV (.csv) | Balance |

## Customization

### Adding New Banks

1. Create a new parser function in `src/bank_parsers.py`:
```python
def parse_newbank_statement(file_path: Path) -> Optional[Dict]:
    # Your parsing logic
    return {
        'bank': 'NewBank',
        'account_number': '...',
        'holder_name': '...',
        'balance': 0.0,
        'fd_amount': 0.0,
        'source_file': file_path.name
    }
```

2. Register it in the `PARSERS` dict and add to the processing pipeline.

## Security Notes

- Bank statements contain sensitive information
- `output/` and `data/` directories are gitignored
- Never commit actual bank data to version control
- Use environment variables for sensitive paths in production

## Troubleshooting

### Issue: "No data found" in web dashboard
**Solution**: Run `python process_all.py` first to generate `output/bank_data.json`

### Issue: Excel file parsing errors
**Solution**: Check file format matches expected structure. Add debug prints in parser functions.

### Issue: Charts not displaying
**Solution**: Ensure Plotly is installed: `pip install plotly`

## Future Enhancements

- [ ] Mutual fund statement parsing
- [ ] FD maturity tracking and alerts
- [ ] Historical trend analysis
- [ ] Email report generation
- [ ] Automated monthly processing

## License

MIT License - See LICENSE file for details

## Contributing

Feel free to open issues or submit pull requests for improvements!
