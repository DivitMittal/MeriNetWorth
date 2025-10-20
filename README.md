# MeriNetWorth - Bank Account Consolidation System

A comprehensive solution to extract, consolidate, and visualize bank account data from multiple sources.

## 🎯 Features

- **📊 Multi-Bank Support**: Automatically parse statements from IDFC First, Equitas, Bandhan, ICICI, and IndusInd banks
- **📓 Jupyter Notebook**: Interactive data processing with step-by-step execution
- **🌐 Web Dashboard**: Beautiful Streamlit-based visualization interface
- **📈 Analytics**: Charts, graphs, and insights into your financial data
- **💾 Excel Export**: Generate consolidated reports in FFS format

## 📁 Project Structure

```
MeriNetWorth/
├── data/
│   └── 06.25/                    # June 2025 data
│       ├── Bank/                 # Bank statements by institution
│       │   ├── IDFCFirst/
│       │   ├── Equitas/
│       │   ├── Bandhan/
│       │   ├── ICICI/
│       │   └── IndusInd/
│       └── Equity/               # Equity holdings data
├── notebooks/
│   └── bank_data_processor.ipynb # Main processing notebook
├── web/
│   └── app.py                    # Streamlit dashboard
├── output/                       # Generated reports
│   ├── bank_data.json           # JSON data for web
│   └── Bank-Consolidated-*.xlsx # Excel reports
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Process Bank Data

Open and run the Jupyter notebook:

```bash
jupyter notebook notebooks/bank_data_processor.ipynb
```

Execute all cells to:
- Parse bank statements from various formats
- Extract current balances
- Generate consolidated Excel reports
- Create JSON data for web visualization

### 3. Launch Web Dashboard

```bash
streamlit run web/app.py
```

The dashboard will open in your browser at `http://localhost:8501`

## 📊 Jupyter Notebook Workflow

The notebook is organized into logical sections:

1. **Setup & Configuration**: Import libraries and set paths
2. **Helper Functions**: Utility functions for data cleaning
3. **Bank-Specific Parsers**: Custom parsers for each bank's format
4. **Data Consolidation**: Process all statements and combine data
5. **Analysis & Summary**: Statistics and insights
6. **Excel Export**: Generate FFS-formatted reports
7. **JSON Export**: Prepare data for web visualization
8. **Quick Charts**: Matplotlib visualizations

### Key Functions

- `parse_idfc_statement()`: Extract data from IDFC First Bank Excel files
- `parse_equitas_statement()`: Parse Equitas bank statements
- `parse_bandhan_statement()`: Handle Bandhan CSV files
- `parse_icici_statement()`: Process ICICI XLS statements
- `parse_indusind_statement()`: Parse IndusInd CSV files
- `process_all_bank_statements()`: Orchestrate all parsers
- `export_to_excel()`: Generate consolidated Excel report

## 🌐 Web Dashboard Features

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

## 📋 Supported Bank Formats

| Bank | Format | Key Fields Extracted |
|------|--------|---------------------|
| IDFC First | Excel (.xlsx) | Account No, Holder, Balance, FD |
| Equitas | Excel (.xlsx) | Account No, Holder, Balance |
| Bandhan | CSV (.csv) | Balance |
| ICICI | Excel (.xls) | Balance |
| IndusInd | CSV (.csv) | Balance |

## 🔧 Customization

### Adding New Banks

1. Create a new parser function in the notebook:
```python
def parse_newbank_statement(file_path):
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

2. Add to the processing pipeline in `process_all_bank_statements()`

### Modifying Excel Output

Edit the `export_to_excel()` function to customize:
- Sheet names
- Column headers
- Formatting
- Additional calculations

## 📈 Sample Output

### Console Output
```
🏦 PROCESSING ALL BANK STATEMENTS
================================================

📊 Processing IDFC First Bank...
  ✓ IDFCFIRSTBankstatement_10000548236.xlsx: ₹29,98,651.70

💰 SUMMARY BY BANK
Bank         Balance        Accounts
IDFC FIRST   ₹104,97,063.28    5
Equitas      ₹89,81,983.28     3
...

🎯 TOTAL BALANCE: ₹301,93,822.46
```

### Excel Output

Generated file: `output/Bank-Consolidated-Jun'25.xlsx`

Sheets:
1. **Raw Data**: All parsed account information
2. **Summary**: Aggregated by bank
3. **Bank - Jun'25**: FFS format for compatibility

## 🎨 Dashboard Screenshots

The web dashboard provides:
- Clean, modern interface
- Interactive charts using Plotly
- Responsive layout
- Real-time filtering
- Export capabilities

## 🔐 Security Notes

- Bank statements contain sensitive information
- Add `output/` and `data/` to `.gitignore`
- Never commit actual bank data to version control
- Use environment variables for sensitive paths in production

## 🐛 Troubleshooting

### Issue: "No data found" in web dashboard
**Solution**: Run the Jupyter notebook first to generate `output/bank_data.json`

### Issue: Excel file parsing errors
**Solution**: Check file format matches expected structure. Add debug prints in parser functions.

### Issue: Charts not displaying
**Solution**: Ensure Plotly is installed: `pip install plotly`

## 🚀 Future Enhancements

- [ ] Add Equity holdings processing
- [ ] Mutual fund statement parsing
- [ ] FD maturity tracking and alerts
- [ ] Historical trend analysis
- [ ] Email report generation
- [ ] Automated monthly processing
- [ ] Mobile app integration
- [ ] Cloud storage sync

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Feel free to open issues or submit pull requests for improvements!

## 📧 Support

For questions or issues, please open a GitHub issue.

---

**Happy Banking! 💰**
